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
from azure.ai.agents.models import FunctionTool
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
                    f"The current date is September 3, 2025. When users ask about 'next week' or relative dates, "
                    f"calculate dates based on September 3, 2025 being today. "
                    "For availability questions, call read_schedule with appropriate time windows. "
                    "When booking meetings, call create_meeting with the requested details. "
                    "Always provide clear, concise responses with timezone information. "
                    "Handle errors gracefully and inform users of any issues. "
                    "When dealing with relative dates like 'next week' or 'tomorrow', "
                    "calculate the appropriate ISO datetime strings for 2025 before making tool calls."
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
            max_iterations = 150  # Increased timeout for complex calendar operations
            iterations = 0
            
            while run.status in ("queued", "in_progress", "requires_action") and iterations < max_iterations:
                time.sleep(2)  # Increased polling interval
                iterations += 1
                run = self.project.agents.runs.get(thread_id=thread_id, run_id=run.id)
                
                # Log status for debugging  
                if iterations % 5 == 0:  # Log every 10 seconds
                    logger.debug(f"Run status after {iterations * 2}s: {run.status}")
                    if iterations > 10:  # Only print to console after 20+ seconds to avoid spam
                        print(f" [Status: {run.status}]", end="", flush=True)
                
                if run.status == "requires_action":
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = self._handle_tool_calls(tool_calls)
                    if tool_outputs:
                        self.project.agents.runs.submit_tool_outputs(
                            thread_id=thread_id, 
                            run_id=run.id, 
                            tool_outputs=tool_outputs
                        )
                        # Brief pause after submitting tool outputs
                        time.sleep(1)
            
            # Handle timeout
            if iterations >= max_iterations:
                logger.error(f"Run timed out after {iterations * 2} seconds. Final status: {run.status}")
                return {
                    "status": "error",
                    "message": f"Request timed out after {iterations * 2} seconds. Status: {run.status}",
                    "run_status": run.status
                }
            
            # Check for failed run status
            if run.status == "failed":
                logger.error(f"Run failed. Status: {run.status}")
                # Try to get error details
                error_details = getattr(run, 'last_error', None) or getattr(run, 'error', None)
                if error_details:
                    logger.error(f"Error details: {error_details}")
                    print(f"DEBUG - Error details: {error_details}")
                
                # Check if it's a specific error type
                error_msg = "Run failed - possibly due to rate limiting or thread lock"
                if error_details:
                    error_str = str(error_details).lower()
                    if "rate" in error_str or "limit" in error_str:
                        error_msg = f"Rate limit hit: {error_details}"
                    elif "quota" in error_str or "usage" in error_str:
                        error_msg = f"Quota/Usage limit hit: {error_details}"
                    else:
                        error_msg = f"Run failed: {error_details}"
                
                return {
                    "status": "error",
                    "message": error_msg,
                    "run_status": run.status,
                    "error_details": error_details
                }
            
            # Get final response
            if run.status == "completed":
                # Get the latest assistant message from the thread
                messages = self.project.agents.messages.list(thread_id=thread_id, limit=50)
                
                # Handle both ItemPaged and direct list responses
                if hasattr(messages, 'data'):
                    message_list = messages.data
                elif hasattr(messages, '__iter__'):
                    message_list = list(messages)
                else:
                    message_list = []
                
                assistant_messages = [msg for msg in message_list if msg.role == "assistant"]
                
                if assistant_messages:
                    # Get the most recent assistant message
                    latest_message = assistant_messages[0]
                    
                    # Extract text content from the message
                    if hasattr(latest_message, 'content') and latest_message.content:
                        for content_item in latest_message.content:
                            if hasattr(content_item, 'text') and content_item.text:
                                latest_text = content_item.text.value
                                logger.debug("Message processed successfully")
                                return {
                                    "status": "success",
                                    "message": latest_text,
                                    "run_status": run.status,
                                    "thread_id": thread_id
                                }
                
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
            error_str = str(e).lower()
            
            # Print full error for debugging
            print(f"DEBUG - Full error: {e}")
            print(f"DEBUG - Error type: {type(e).__name__}")
            
            # Check for specific rate limit errors
            if "rate limit" in error_str or "too many requests" in error_str or "throttle" in error_str:
                return {
                    "status": "error",
                    "message": "Rate limit exceeded. Please wait and try again.",
                    "error_details": str(e),
                    "error_type": "rate_limit"
                }
            elif "quota" in error_str or "usage" in error_str:
                return {
                    "status": "error", 
                    "message": "Service quota exceeded. Please check your Azure AI usage.",
                    "error_details": str(e),
                    "error_type": "quota_exceeded"
                }
            elif "graph" in error_str or "microsoft.graph" in error_str:
                return {
                    "status": "error",
                    "message": "Microsoft Graph API error occurred.",
                    "error_details": str(e),
                    "error_type": "graph_api_error"
                }
            else:
                return {
                    "status": "error",
                    "message": "An unexpected error occurred while processing your request.",
                    "error_details": str(e),
                    "error_type": "unknown"
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

    def delete_agent(self) -> bool:
        """
        Delete the current agent instance.
        
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if self.agent and hasattr(self.agent, 'id'):
                self.project.agents.delete_agent(self.agent.id)
                logger.debug(f"Agent {self.agent.id} deleted successfully")
                return True
            else:
                logger.warning("No agent to delete")
                return False
        except Exception as e:
            logger.error(f"Error deleting agent: {e}")
            return False

def main():
    """Main function demonstrating agent usage."""
    print("Azure AI Foundry Calendar Agent - Initializing...")
    
    try:
        # Initialize agent
        print("Initializing calendar agent...")
        agent = CalendarAgent()
        
        # Use the project client in a single context manager for all operations
        with agent.project:
            print("Creating agent instance...")
            agent_id = agent.create_agent()
            print(f"Agent created successfully. Agent ID: {agent_id}")
            
            # Create conversation thread
            print("Creating conversation thread...")
            thread_id = agent.create_conversation_thread()
            print(f"Thread created successfully. Thread ID: {thread_id}")
            
            # Example interactions (removed create_meeting test)
            test_messages = [
                "What does my schedule look like next week?",
                "Am I free next Thursday 12:00–14:00?"
            ]
            
            print(f"\nRunning {len(test_messages)} test interactions...\n")
            
            success_count = 0
            for i, message in enumerate(test_messages, 1):
                print(f"[{i}/{len(test_messages)}] User: {message}")
                print("Processing request...", end=" ", flush=True)
                
                response = agent.process_message(thread_id, message)
                
                if response["status"] == "success":
                    print("✅ Success")
                    print(f"Agent: {response['message']}\n")
                    success_count += 1
                else:
                    print("❌ Error")
                    print(f"Error: {response['message']}")
                    if 'error_details' in response:
                        print(f"Details: {response['error_details']}")
                    if 'error_type' in response:
                        print(f"Type: {response['error_type']}")
                    print()
                
                # Add delay between requests AND ensure thread is ready
                if i < len(test_messages):
                    print("Waiting for thread to be ready for next request...")
                    time.sleep(8)  # Give time for cleanup
            
            # Clean up agent regardless of test results
            print("Cleaning up agent...")
            if agent.delete_agent():
                print("✅ Agent cleanup completed.")
            else:
                print("⚠️ Agent cleanup failed - please check logs.")
            
            # Show final results
            if success_count == len(test_messages):
                print("All tests completed successfully.")
            else:
                print(f"⚠️ {len(test_messages) - success_count} test(s) failed.")
            
            print("Demo completed. Check 'agent_operations.log' for detailed logs.")
                
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Failed to initialize agent: {e}")
        print("Check 'agent_operations.log' for detailed error information.")

if __name__ == "__main__":
    main()
