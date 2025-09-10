"""
Interactive Calendar Agent Chat Interface
Maintains all the detailed logging and API visibility from enhanced_agent.py
with beautiful terminal formatting for calendar events.
"""
import sys
import signal
import re
import logging
import time
from datetime import datetime
from enhanced_agent import CalendarAgent

# Configure clean logging for interactive chat
# Suppress verbose Azure SDK and third-party library logging
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.identity._credentials').setLevel(logging.WARNING)
logging.getLogger('azure.identity._credentials.environment').setLevel(logging.WARNING)
logging.getLogger('azure.identity._credentials.managed_identity').setLevel(logging.WARNING)
logging.getLogger('azure.identity._credentials.chained').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

# Configure root logger for clean output
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)

# Only show important messages from our app - but send to file, not console
logging.getLogger('enhanced_agent').setLevel(logging.INFO)
logging.getLogger('approval_callback').setLevel(logging.WARNING)  # Hide approval_callback logs from console

# Create file handler for all logs
file_handler = logging.FileHandler('chat_session.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger('approval_callback').addHandler(file_handler)

# Try to import colorama for cross-platform terminal colors
try:
    from colorama import init, Fore, Style, Back
    has_colors = True
    init()  # Initialize colorama
except ImportError:
    print("For prettier output, install colorama: pip install colorama")
    # Create dummy color objects if colorama isn't available
    class DummyColors:
        def __getattr__(self, name):
            return ""
    Fore = Style = Back = DummyColors()
    has_colors = False

# Global variable for agent reference in signal handler
_agent_ref = None

def format_markdown_message(text):
    """Format text with proper colorama colors instead of markdown asterisks."""
    
    formatted = text
    
    # Replace markdown bold with colorama formatting
    # **Text** becomes colored bold text
    formatted = re.sub(r'\*\*(.*?)\*\*', f'{Fore.WHITE}{Style.BRIGHT}\\1{Style.RESET_ALL}', formatted)
    
    # Color specific approval-related content
    if "APPROVAL UPDATE" in formatted:
        # Color the status
        formatted = re.sub(r'❌ REJECTED', f'{Fore.RED}{Style.BRIGHT}❌ REJECTED{Style.RESET_ALL}', formatted)
        formatted = re.sub(r'✅ APPROVED', f'{Fore.GREEN}{Style.BRIGHT}✅ APPROVED{Style.RESET_ALL}', formatted)
        
        # Color the sections
        formatted = re.sub(r'📋 (.*?):', f'{Fore.CYAN}{Style.BRIGHT}📋 \\1:{Style.RESET_ALL}', formatted)
        formatted = re.sub(r'- (Request ID|Status|Manager\'s Response|Processed):', f'{Fore.YELLOW}- \\1:{Style.RESET_ALL}', formatted)
    
    # Color calendar event titles
    formatted = re.sub(r'(\d+\.\s+)(.*?)(\s+\()', f'\\1{Fore.CYAN}{Style.BRIGHT}\\2{Style.RESET_ALL}\\3', formatted)
    
    # Color specific field labels
    formatted = re.sub(r'(Time|Location|Organiser):', f'{Fore.YELLOW}\\1:{Style.RESET_ALL}', formatted)
    
    # Color leave request details
    formatted = re.sub(r'- (Leave Period|Reason|Manager\'s Email|Calendar Status):', f'{Fore.YELLOW}- \\1:{Style.RESET_ALL}', formatted)
    
    # Color success/error indicators
    formatted = re.sub(r'✅', f'{Fore.GREEN}✅{Style.RESET_ALL}', formatted)
    formatted = re.sub(r'❌', f'{Fore.RED}❌{Style.RESET_ALL}', formatted)
    formatted = re.sub(r'🔔', f'{Fore.CYAN}🔔{Style.RESET_ALL}', formatted)
    
    return formatted

def print_welcome():
    """Print welcome message and sample queries."""
    today = datetime.now()
    
    print("\n" + "=" * 60)
    print(f"{Fore.CYAN}{Style.BRIGHT}🗓️  CALENDAR AGENT CHAT{Style.RESET_ALL}")
    print("=" * 60)
    print(f"📅 {today.strftime('%A, %B %d, %Y')}")
    print()
    print(f"{Fore.YELLOW}SAMPLE QUERIES:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}• What's my schedule today?")
    print(f"• Am I free tomorrow 2-3pm?") 
    print(f"• Book meeting with john@company.com at 3pm{Style.RESET_ALL}")
    print()
    print(f"Type {Fore.RED}'quit'{Style.RESET_ALL} to exit")
    print(f"{Style.DIM}Note: Calendar events will be displayed with colored formatting{Style.RESET_ALL}")
    print("=" * 60)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n👋 Goodbye! Attempting agent cleanup...")
    try:
        global _agent_ref
        if _agent_ref:
            if _agent_ref.delete_agent():
                print("✅ Agent deleted successfully.")
            else:
                print("⚠️  Agent deletion failed - check logs.")
    except Exception as cleanup_error:
        print(f"❌ Error during agent cleanup: {cleanup_error}")
    sys.exit(0)

def main():
    """Main chat loop with enhanced_agent.py functionality."""
    # Set up signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)
    
    print_welcome()
    
    global _agent_ref
    _agent_ref = None
    thread_id = None
    try:
        # Initialize agent
        print("🚀 Initializing Calendar Agent...")
        _agent_ref = CalendarAgent()
        
        # Import callback service for notifications
        from approval_callback import callback_service
        
        # Create agent and thread
        with _agent_ref.project:
            agent_id = _agent_ref.create_agent()
            print(f"✅ Agent created: {agent_id}")
            
            thread_id = _agent_ref.create_conversation_thread()
            print(f"✅ Thread created: {thread_id}")
            print("\n🎉 Ready! Start chatting:")
            print("-" * 60)
            
            # Interactive chat loop
            while True:
                try:
                    # Get user input first
                    user_input = input(f"\n{Fore.BLUE}👤 You: {Style.RESET_ALL}").strip()
                    
                    # Check for exit commands
                    if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                        print("\n👋 Goodbye!")
                        break
                        
                    if not user_input:
                        continue
                    
                    # Check if user is asking about approval status to avoid duplicate notifications
                    is_status_check = any(keyword in user_input.lower() for keyword in 
                                        ['check', 'status', 'request', 'approval', 'update'])
                    
                    # Only show automatic notifications if user is not actively checking status
                    if not is_status_check:
                        notification_result = callback_service.check_notifications()
                        if notification_result.get("has_notifications"):
                            for notification in notification_result.get("notifications", []):
                                if notification.get("type") == "approval_update":
                                    # Simple notification format
                                    status = notification.get("status", "").upper()
                                    approval_id = notification.get("approval_id", "")
                                    
                                    # Get leave details from the stored request
                                    stored_request = callback_service.get_approval_status(approval_id)
                                    leave_period = "your leave request"
                                    
                                    if stored_request and stored_request.get("status") == "success":
                                        request_details = stored_request.get("request_details", {})
                                        start_date = request_details.get("leave_start_date", "")
                                        end_date = request_details.get("leave_end_date", "")
                                        if start_date and end_date:
                                            leave_period = f"your leave application from {start_date} to {end_date}"
                                    
                                    if status == "APPROVED":
                                        print(f"\n{Fore.GREEN}{Style.BRIGHT}NOTIFICATION:{Style.RESET_ALL} {leave_period} was {Fore.GREEN}{Style.BRIGHT}approved{Style.RESET_ALL} by your manager")
                                    elif status == "REJECTED":
                                        print(f"\n{Fore.RED}{Style.BRIGHT}NOTIFICATION:{Style.RESET_ALL} {leave_period} was {Fore.RED}{Style.BRIGHT}rejected{Style.RESET_ALL} by your manager")
                                    else:
                                        print(f"\n{Fore.CYAN}{Style.BRIGHT}NOTIFICATION:{Style.RESET_ALL} {leave_period} status has been updated")
                            
                            # Clear the notifications after showing them
                            callback_service.clear_shown_notifications()
                    
                    # Process message
                    print("🔄 Processing...", end=" ", flush=True)
                    response = _agent_ref.process_message(thread_id, user_input)
                    
                    if response["status"] == "success":
                        print("✅")
                        formatted_message = format_markdown_message(response['message'])
                        print(f"🤖 Agent:\n{formatted_message}")
                        
                        # Check for notifications immediately after agent response (for real-time approval notifications)
                        time.sleep(0.5)  # Brief pause to allow any async notifications to arrive
                        notification_result = callback_service.check_notifications()
                        if notification_result.get("has_notifications"):
                            for notification in notification_result.get("notifications", []):
                                if notification.get("type") == "approval_update":
                                    # Simple notification format
                                    status = notification.get("status", "").upper()
                                    approval_id = notification.get("approval_id", "")
                                    
                                    # Get leave details from the stored request
                                    stored_request = callback_service.get_approval_status(approval_id)
                                    leave_period = "your leave request"
                                    
                                    if stored_request and stored_request.get("status") == "success":
                                        request_details = stored_request.get("request_details", {})
                                        start_date = request_details.get("leave_start_date", "")
                                        end_date = request_details.get("leave_end_date", "")
                                        if start_date and end_date:
                                            leave_period = f"your leave application from {start_date} to {end_date}"
                                    
                                    if status == "APPROVED":
                                        print(f"\n{Fore.GREEN}{Style.BRIGHT}NOTIFICATION:{Style.RESET_ALL} {leave_period} was {Fore.GREEN}{Style.BRIGHT}approved{Style.RESET_ALL} by your manager")
                                    elif status == "REJECTED":
                                        print(f"\n{Fore.RED}{Style.BRIGHT}NOTIFICATION:{Style.RESET_ALL} {leave_period} was {Fore.RED}{Style.BRIGHT}rejected{Style.RESET_ALL} by your manager")
                                    else:
                                        print(f"\n{Fore.CYAN}{Style.BRIGHT}NOTIFICATION:{Style.RESET_ALL} {leave_period} status has been updated")
                            
                            # Clear the notifications after showing them
                            callback_service.clear_shown_notifications()
                    else:
                        print("❌")
                        print(f"❌ Error: {response['message']}")
                        if 'error_details' in response:
                            print(f"Details: {response['error_details']}")
                except EOFError:
                    print("\n👋 Session ended.")
                    break
                except KeyboardInterrupt:
                    print("\n👋 Session interrupted.")
                    break
            
            # Cleanup
            print("\n🧹 Cleaning up...")
            if _agent_ref.delete_agent():
                print("✅ Cleanup completed.")
            else:
                print("⚠️  Cleanup failed - check logs.")
            print("📝 Check 'agent_operations.log' for detailed logs.")
            print("=" * 60)
    
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("Check your environment variables and network connection.")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
