"""
Enhanced Azure AI Foundry agent implementation with proper error handling,
logging, and production-ready features.
"""
import os
import time
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, MessageRole  # CHANGED: import MessageRole
from improved_tools import read_schedule, create_meeting

# Configure logging - detailed logs to file, minimal to console
file_handler = logging.FileHandler('agent_operations.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Validate required environment variables
REQUIRED_ENV_VARS = ["PROJECT_ENDPOINT", "MODEL_DEPLOYMENT_NAME"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {missing_vars}")

class CalendarAgent:
    """Enhanced Calendar Agent with proper error handling and logging."""
    
    def __init__(self):
        """Initialize the Calendar Agent."""
        self.project = None
        self.agent = None
        self.tools = None
        self._initialize_tools()
        self._initialize_client()
        
    def _initialize_tools(self):
        """Initialize function tools."""
        try:
            self.tools = FunctionTool(functions={read_schedule, create_meeting})
            logger.debug("Function tools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize function tools: {e}")
            raise
            
    def _initialize_client(self):
        """Initialize Azure AI Project Client."""
        try:
            credential = DefaultAzureCredential()
            self.project = AIProjectClient(
                endpoint=os.environ["PROJECT_ENDPOINT"], 
                credential=credential
            )
            logger.debug("Azure AI Project Client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure AI Project Client: {e}")
            raise
            
    def create_agent(self, name: str = "CalendarAgent") -> str:
        """
        Create a new agent instance.
        
        Args:
            name: Name for the agent
            
        Returns:
            Agent ID
        """
        try:
            self.agent = self.project.agents.create_agent(
                model=os.environ["MODEL_DEPLOYMENT_NAME"],
                name=name,
                instructions=(
                    "You are a professional calendar assistant that helps users manage their schedules. "
                    "For availability questions, call read_schedule with appropriate time windows. "
                    "When booking meetings, call create_meeting with the requested details. "
                    "Always provide clear, concise responses with timezone information. "
                    "Handle errors gracefully and inform users of any issues. "
                    "When dealing with relative dates like 'next week' or 'tomorrow', "
                    "calculate the appropriate ISO datetime strings before making tool calls."
                ),
                tools=self.tools.definitions,
            )
                
            logger.debug(f"Agent '{name}' created successfully with ID: {self.agent.id}")
            return self.agent.id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise
            
    def create_conversation_thread(self) -> str:
        """
        Create a new conversation thread.
        
        Returns:
            Thread ID
        """
        try:
            thread = self.project.agents.threads.create()
            logger.debug(f"Conversation thread created with ID: {thread.id}")
            return thread.id
        except Exception as e:
            logger.error(f"Failed to create conversation thread: {e}")
            raise
            
    def process_message(self, thread_id: str, message: str) -> Dict[str, Any]:
        """
        Process a user message and return the agent's response.
        
        Args:
            thread_id: Thread ID for the conversation
            message: User message
            
        Returns:
            Dict containing response and metadata
        """
        logger.debug(f"Processing message in thread {thread_id}: {message[:100]}...")
        
        try:
            # Add user message to thread
            self.project.agents.messages.create(
                thread_id=thread_id, 
                role="user", 
                content=message
            )
            
            # Create and execute run
            run = self.project.agents.runs.create(
                thread_id=thread_id, 
                agent_id=self.agent.id
            )
            
            # Monitor run execution with timeout
            max_iterations = 60  # keep as-is (can increase later if needed)
            iterations = 0
            
            while run.status in ("queued", "in_progress", "requires_action") and iterations < max_iterations:
                time.sleep(1)
                iterations += 1
                run = self.project.agents.runs.get(thread_id=thread_id, run_id=run.id)
                
                if run.status == "requires_action":
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = self._handle_tool_calls(tool_calls)
                    if tool_outputs:
                        self.project.agents.runs.submit_tool_outputs(
                            thread_id=thread_id, 
                            run_id=run.id, 
                            tool_outputs=tool_outputs
                        )
            
            # Handle timeout
            if iterations >= max_iterations:
                logger.error(f"Run timed out after {max_iterations} seconds")
                return {
                    "status": "error",
                    "message": "Request timed out. Please try again.",
                    "run_status": run.status
                }
            
            # Get final response
            if run.status == "completed":
                # CHANGED: use helper to get the latest assistant text
                latest_text = self.project.agents.messages.get_last_message_text_by_role(
                    thread_id=thread_id,
                    role=MessageRole.ASSISTANT
                )
                if latest_text is not None:
                    logger.debug("Message processed successfully")
                    return {
                        "status": "success",
                        "message": latest_text,
                        "run_status": run.status,
                        "thread_id": thread_id
                    }
                else:
                    logger.warning("No assistant response found")
                    return {
                        "status": "error",
                        "message": "No response generated",
                        "run_status": run.status
                    }
            else:
                logger.error(f"Run failed with status: {run.status}")
                return {
                    "status": "error",
                    "message": f"Processing failed with status: {run.status}",
                    "run_status": run.status
                }
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "status": "error",
                "message": "An unexpected error occurred while processing your request.",
                "error_details": str(e)
            }
            
    def _handle_tool_calls(self, tool_calls) -> List[Dict[str, Any]]:
        """
        Handle tool calls from the agent.
        
        Args:
            tool_calls: List of tool calls to execute
            
        Returns:
            List of tool outputs
        """
        outputs = []
        
        for call in tool_calls:
            try:
                fn = call.function.name
                args = json.loads(call.function.arguments)
                
                logger.debug(f"Executing tool call: {fn} with args: {list(args.keys())}")
                
                if fn == "read_schedule":
                    result = read_schedule(**args)
                    outputs.append({
                        "tool_call_id": call.id, 
                        "output": json.dumps(result)
                    })
                    
                elif fn == "create_meeting":
                    result = create_meeting(**args)
                    outputs.append({
                        "tool_call_id": call.id, 
                        "output": json.dumps(result)
                    })
                    
                else:
                    logger.warning(f"Unknown function called: {fn}")
                    outputs.append({
                        "tool_call_id": call.id, 
                        "output": json.dumps({
                            "error": "unknown_function", 
                            "message": f"Function {fn} is not supported"
                        })
                    })
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in function arguments: {e}")
                outputs.append({
                    "tool_call_id": call.id, 
                    "output": json.dumps({
                        "error": "invalid_arguments", 
                        "message": "Invalid function arguments"
                    })
                })
                
            except Exception as e:
                logger.error(f"Error executing tool call {fn}: {e}")
                outputs.append({
                    "tool_call_id": call.id, 
                    "output": json.dumps({
                        "error": "execution_error", 
                        "message": f"Error executing {fn}: {str(e)}"
                    })
                })
                
        return outputs

def main():
    """Main function demonstrating agent usage."""
    print("🤖 Azure AI Foundry Calendar Agent - Starting...")
    
    try:
        # Initialize agent
        print("🔧 Initializing agent...")
        agent = CalendarAgent()
        
        # Use the project client in a single context manager for all operations
        with agent.project:
            print("✅ Creating agent...")
            agent_id = agent.create_agent()
            print(f"✅ Agent created successfully!")
            
            # Create conversation thread
            print("🧵 Creating conversation thread...")
            thread_id = agent.create_conversation_thread()
            print("✅ Thread created successfully!")
            
            # Example interactions
            test_messages = [
                "What does my schedule look like next week?",
                "Am I free next Thursday 12:00–14:00?",
                "Book a 30-minute catch-up with alex@contoso.com next Thursday at 12:30, title 'Design sync'."
            ]
            
            print(f"\n📝 Running {len(test_messages)} test interactions...\n")
            
            for i, message in enumerate(test_messages, 1):
                print(f"[{i}/{len(test_messages)}] 🔵 User: {message}")
                print("🤔 Processing...", end=" ", flush=True)
                
                response = agent.process_message(thread_id, message)
                
                if response["status"] == "success":
                    print("✅ Success!")
                    print(f"🤖 Agent: {response['message']}\n")
                else:
                    print("❌ Error!")
                    print(f"❌ {response['message']}\n")
            
            print("🎉 Demo completed! Check 'agent_operations.log' for detailed logs.")
                
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Failed to initialize agent: {e}")
        print("💡 Check 'agent_operations.log' for detailed error information.")

if __name__ == "__main__":
    main()
