"""
Enhanced Azure AI Foundry agent implementation with proper error handling,
logging, and production-ready features.
"""
import os
import time
import json
import logging
import asyncio
import uuid
from typing import Dict, Any, List
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
from tools.email_tools import read_schedule, create_meeting
from tools.datetime_tool import get_current_datetime
from approval_callback import callback_service, start_callback_server_background

# Configure logging - detailed logs to debugging_logs folder, minimal to console
import os
log_dir = 'debugging_logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

file_handler = logging.FileHandler(os.path.join(log_dir, 'agent.log'))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)  # Only errors to console - reduce clutter
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
    """Enhanced Calendar Agent with Logic App approval workflow integration."""
    
    def __init__(self):
        """Initialize the Calendar Agent with Logic App integration."""
        self.project = None
        self.agent = None
        self.tools = None
        self.logic_app_tool = None
        self.approval_functions = {}
        self._initialize_logic_app()
        self._initialize_tools()
        self._initialize_client()
        self._start_callback_service()
        
    def _initialize_logic_app(self):
        """Initialize Logic App integration."""
        try:
            # Get Logic App HTTP URL from environment (simplified approach)
            logic_app_url = os.getenv("LOGIC_APP_HTTP_URL")
            
            if logic_app_url:
                from tools.logic_app_tool import (
                    SimpleLogicAppTool, 
                    create_send_approval_email_function, 
                    create_leave_request_function
                )
                
                # Initialize the simplified Logic App tool
                self.logic_app_tool = SimpleLogicAppTool(logic_app_url)
                
                # Create approval functions
                self.approval_functions = {
                    "send_approval_email": create_send_approval_email_function(self.logic_app_tool),
                    "request_leave_approval": create_leave_request_function(self.logic_app_tool)
                }
                
                logger.info("Logic App integration initialized successfully")
            else:
                logger.info("Logic App URL not configured - running without approval features")
                self.logic_app_tool = None
                
        except Exception as e:
            logger.error(f"Failed to initialize Logic App integration: {e}")
            self.logic_app_tool = None
    
    def _start_callback_service(self):
        """Start the callback service for handling Logic App responses."""
        try:
            start_callback_server_background()
            logger.info("Approval callback service started")
        except Exception as e:
            logger.warning(f"Could not start callback service: {e}")
        
    def _initialize_tools(self):
        """Initialize function tools including Logic App functions."""
        try:
            # Base calendar tools
            # Initialize tools
            base_functions = {read_schedule, create_meeting, get_current_datetime}
            
            # Add approval status checking function
            def check_approval_status(approval_id: str = None) -> Dict[str, Any]:
                """Check the status of a leave approval request."""
                if approval_id and callback_service:
                    return callback_service.get_approval_status(approval_id)
                elif callback_service:
                    # If no specific ID provided, check for any recent notifications
                    notifications = callback_service.check_notifications()
                    if notifications.get("has_notifications"):
                        recent_approvals = []
                        for notif in notifications.get("notifications", []):
                            if notif.get("type") == "approval_update":
                                recent_approvals.append({
                                    "approval_id": notif.get("approval_id"),
                                    "status": notif.get("status"),
                                    "message": notif.get("message"),
                                    "formatted_message": notif.get("message", "")
                                })
                        if recent_approvals:
                            return {
                                "status": "success",
                                "message": "Found recent approval updates",
                                "recent_approvals": recent_approvals
                            }
                    return {
                        "status": "success", 
                        "message": "No recent approval updates found"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Approval service not available"
                    }
            
            # Add the function properly to the base functions set
            base_functions.add(check_approval_status)
            
            # Add approval functions if Logic App is available
            if self.logic_app_tool and self.approval_functions:
                all_functions = base_functions.union(set(self.approval_functions.values()))
                logger.debug("Function tools initialized with Logic App approval functions")
            else:
                all_functions = base_functions
                logger.debug("Function tools initialized without Logic App functions")
            
            self.tools = FunctionTool(functions=all_functions)
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
            agent_obj = self.project.agents.create_agent(
                model=os.environ["MODEL_DEPLOYMENT_NAME"],
                name=name,
                instructions=(
                    "You are a professional calendar assistant with approval workflow capabilities. "
                    "ALWAYS call get_current_datetime() first to get the current date and time before answering any questions. "
                    "Use the returned date information for all relative date calculations (today, tomorrow, next week, etc.). "
                    
                    "## Calendar Management Instructions:"
                    "For schedule queries, you MUST format each event EXACTLY as follows:"
                    "\n1. **<Event Title>**"
                    "\n   - **Time:** <Start Time> to <End Time>"
                    "\n   - **Location:** <Location>"
                    "\n   - **Organiser:** <Organiser Name> (<Organiser Email>)"
                    "\nThe organizer information is in the response under event.organizer.emailAddress.name and event.organizer.emailAddress.address."
                    
                    "## Meeting Creation Instructions:"
                    "When booking meetings, you MUST summarize all meeting details to the user in a clear, formatted block and ask for explicit confirmation. "
                    "You must wait for the user to type 'yes' to proceed with booking or 'no' to cancel. Do not call create_meeting until receiving a 'yes'."
                    
                    "## Approval Workflow Instructions:"
                    "You now have access to approval workflow functions for leave requests and meeting approvals. Use these when:"
                    "1. **Leave Requests**: When a user wants to request time off:"
                    "   - First check their calendar using read_schedule() to identify potential conflicts"
                    "   - Gather all required information: start date, end date, reason, manager email"
                    "   - IMPORTANT: Present a complete summary of the leave request to the user"
                    "   - Ask for explicit confirmation before submitting: 'Should I submit this leave request for approval?'"
                    "   - When calling request_leave_approval(), include calendar_status parameter with clear conflict information"
                    "   - Example calendar_status: 'Calendar checked - no conflicts found' or 'Calendar conflict: Meeting with John at 2pm on Nov 15'"
                    "   - Only call request_leave_approval() function AFTER user confirms with 'yes' or similar"
                    
                    "2. **Meeting Approvals**: When a user wants to schedule a meeting that requires approval:"
                    "   - Gather all meeting details first"
                    "   - Present a complete summary to the user"
                    "   - Ask for explicit confirmation before submitting for approval"
                    "   - Only call send_approval_email() AFTER user confirms"
                    
                    "3. **Calendar Conflict Checking**: Before any leave or meeting requests, always check the user's calendar first"
                    "   - Use read_schedule() to check for existing appointments"
                    "   - Inform the user of any conflicts before proceeding with approval requests"
                    
                    "## CRITICAL: User Confirmation Required:"
                    "NEVER automatically submit approval requests. Always:"
                    "1. Present complete request details to user"
                    "2. Ask 'Should I submit this [leave request/meeting approval] for approval?'"
                    "3. Wait for user confirmation (yes/approve/confirm/submit)"
                    "4. Only then call the approval function"
                    
                    "## Response Guidelines:"
                    "- Always provide clear, concise responses with timezone information"
                    "- Handle errors gracefully and inform users of any issues"
                    "- When approval workflows are triggered, explain to the user what will happen next"
                    "- Provide approval tracking information when available"
                    "- When users ask about approval status, use check_approval_status() function to get current status"
                    "- If an approval has been processed, inform the user immediately with the current status"
                    
                    "## Example Approval Workflow:"
                    "When user says 'I want to take leave next week', you should:"
                    "1. Call get_current_datetime() to understand 'next week'"
                    "2. Call read_schedule() to check for existing appointments"
                    "3. Ask for missing details (reason, manager email, specific dates)"
                    "4. Present complete leave request summary to user"
                    "5. Ask: 'Should I submit this leave request for approval?'"
                    "6. Only call request_leave_approval() if user confirms"
                    "7. Explain the approval process to the user"
                ),
                tools=self.tools.definitions,
            )
            self.agent = agent_obj
            logger.debug(f"Agent '{name}' created successfully with ID: {agent_obj.id}")
            return agent_obj.id
            
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
            
            # Check for specific rate limit errors
            if "rate limit" in error_str or "too many requests" in error_str or "throttle" in error_str:
                return {
                    "status": "error",
                    "message": "Rate limit exceeded. Please wait and try again.",
                    "error_details": str(e)
                }
            elif "quota" in error_str:
                return {
                    "status": "error", 
                    "message": "Service quota exceeded. Please check your Azure AI usage.",
                    "error_details": str(e)
                }
            else:
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
                    
                elif fn == "get_current_datetime":
                    result = get_current_datetime(**args)
                    outputs.append({
                        "tool_call_id": call.id,
                        "output": json.dumps(result)
                    })
                
                elif fn == "check_approval_status":
                    # Call the check_approval_status function directly
                    if callback_service:
                        approval_id = args.get("approval_id")
                        if approval_id:
                            result = callback_service.get_approval_status(approval_id)
                        else:
                            # Check for any recent notifications
                            notifications = callback_service.check_notifications()
                            if notifications.get("has_notifications"):
                                recent_approvals = []
                                for notif in notifications.get("notifications", []):
                                    if notif.get("type") == "approval_update":
                                        recent_approvals.append({
                                            "approval_id": notif.get("approval_id"),
                                            "status": notif.get("status"),
                                            "message": notif.get("message"),
                                            "formatted_message": notif.get("message", "")
                                        })
                                if recent_approvals:
                                    result = {
                                        "status": "success",
                                        "message": "Found recent approval updates",
                                        "recent_approvals": recent_approvals
                                    }
                                else:
                                    result = {
                                        "status": "success", 
                                        "message": "No recent approval updates found"
                                    }
                            else:
                                result = {
                                    "status": "success", 
                                    "message": "No recent approval updates found"
                                }
                    else:
                        result = {
                            "status": "error",
                            "message": "Approval service not available"
                        }
                    
                    outputs.append({
                        "tool_call_id": call.id,
                        "output": json.dumps(result)
                    })
                
                elif fn == "send_approval_email" and self.approval_functions.get(fn):
                    # Handle Logic App approval email
                    approval_id = str(uuid.uuid4())
                    
                    # Register the approval request
                    callback_url = callback_service.register_approval_request(
                        approval_id, 
                        {"type": "approval_email", "details": args}
                    )
                    
                    # Add callback URL to args
                    args["callback_url"] = callback_url
                    
                    # Call the approval function
                    result = asyncio.run(self.approval_functions[fn](**args))
                    
                    # Add approval tracking info
                    result["approval_id"] = approval_id
                    result["callback_url"] = callback_url
                    
                    outputs.append({
                        "tool_call_id": call.id,
                        "output": json.dumps(result)
                    })
                
                elif fn == "request_leave_approval" and self.approval_functions.get(fn):
                    # Handle Logic App leave approval
                    approval_id = str(uuid.uuid4())
                    
                    # Register the approval request
                    callback_url = callback_service.register_approval_request(
                        approval_id,
                        {"type": "leave_request", "details": args}
                    )
                    
                    # Add callback URL to args
                    args["callback_url"] = callback_url
                    
                    # Call the leave approval function
                    result = asyncio.run(self.approval_functions[fn](**args))
                    
                    # Add approval tracking info
                    result["approval_id"] = approval_id
                    result["callback_url"] = callback_url
                    
                    # Add user-friendly message about the approval process
                    if result.get("status") == "success":
                        result["user_message"] = (
                            f"✅ Leave request submitted successfully!\n"
                            f"📧 Approval email sent to manager\n"
                            f"🔄 Approval ID: {approval_id}\n"
                            f"⏳ You will be notified once your manager responds\n"
                            f"📞 If urgent, you can follow up directly with your manager"
                        )
                    
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
                agent_id = self.agent.id
                try:
                    self.project.agents.delete_agent(agent_id)
                    logger.debug(f"Agent {agent_id} deleted successfully")
                    return True
                except Exception as api_error:
                    logger.error(f"Azure API error deleting agent {agent_id}: {api_error}")
                    return False
            else:
                logger.warning("No agent to delete (self.agent is None or missing id)")
                return False
        except Exception as e:
            logger.error(f"General error deleting agent: {e}")
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
                    print("Success")
                    print(f"Agent: {response['message']}\n")
                    success_count += 1
                else:
                    print("Error")
                    print(f"Error: {response['message']}\n")
                
                # Add delay between requests AND ensure thread is ready
                if i < len(test_messages):
                    print("Waiting for thread to be ready for next request...")
                    time.sleep(8)  # Give time for cleanup
            
            # Clean up agent regardless of test results
            print("Cleaning up agent...")
            if agent.delete_agent():
                print("Agent cleanup completed.")
            else:
                print("Agent cleanup failed - please check logs.")
            
            # Show final results
            if success_count == len(test_messages):
                print("All tests completed successfully.")
            else:
                print(f"{len(test_messages) - success_count} test(s) failed.")
            
            print("Demo completed. Check 'debugging_logs/agent.log' for detailed logs.")
                
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"Failed to initialize agent: {e}")
        print("Check 'debugging_logs/agent.log' for detailed error information.")

if __name__ == "__main__":
    main()
