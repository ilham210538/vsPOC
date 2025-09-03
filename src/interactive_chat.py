"""
Interactive Calendar Agent Chat Interface
Maintains all the detailed logging and API visibility from enhanced_agent.py
with beautiful terminal formatting for calendar events.
"""
import sys
import signal
import re
from datetime import datetime
from enhanced_agent import CalendarAgent

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
    """Format markdown text with basic terminal styling. Keeps the original formatting intact."""
    
    # Simple formatting - just enhance the calendar events without altering content
    formatted = text
    
    # Make event titles stand out
    formatted = re.sub(r'(\d+\.\s+)\*\*(.*?)\*\*', f'\\1{Fore.CYAN}{Style.BRIGHT}\\2{Style.RESET_ALL}', formatted)
    
    # Highlight important fields
    formatted = re.sub(r'\*\*Time:\*\*', f'{Fore.YELLOW}**Time:**{Style.RESET_ALL}', formatted)
    formatted = re.sub(r'\*\*Location:\*\*', f'{Fore.GREEN}**Location:**{Style.RESET_ALL}', formatted)
    formatted = re.sub(r'\*\*Organiser:\*\*', f'{Fore.MAGENTA}**Organiser:**{Style.RESET_ALL}', formatted)
    
    # Add some emoji for visual appeal
    formatted = re.sub(r'(^\d+\.\s+)', r'\1 ', formatted, flags=re.MULTILINE)
    
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
                    # Get user input
                    user_input = input("\n👤 You: ").strip()
                    
                    # Check for exit commands
                    if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                        print("\n👋 Goodbye!")
                        break
                        
                    if not user_input:
                        continue
                    
                    # Process message
                    print("🔄 Processing...", end=" ", flush=True)
                    response = _agent_ref.process_message(thread_id, user_input)
                    
                    if response["status"] == "success":
                        print("✅")
                        formatted_message = format_markdown_message(response['message'])
                        print(f"🤖 Agent:\n{formatted_message}")
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
