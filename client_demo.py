"""
Client Demonstration Script for Azure AI Foundry Calendar Agent

This script demonstrates the complete functionality of the Calendar Agent
for client presentations, including error handling and monitoring capabilities.
"""
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from enhanced_agent import CalendarAgent
except ImportError:
    print("❌ Error: Could not import enhanced agent. Make sure all dependencies are installed.")
    sys.exit(1)

class ClientDemo:
    """Demonstration class for client presentations."""
    
    def __init__(self):
        """Initialize the demo."""
        self.agent = None
        self.thread_id = None
        
    def setup_demo(self) -> bool:
        """Set up the demo environment."""
        print("🔧 Setting up Azure AI Foundry Calendar Agent Demo...")
        
        try:
            # Initialize agent
            self.agent = CalendarAgent()
            agent_id = self.agent.create_agent("ClientDemo-CalendarAgent")
            print(f"✅ Agent created successfully (ID: {agent_id[:8]}...)")
            
            # Create conversation thread
            self.thread_id = self.agent.create_conversation_thread()
            print(f"✅ Conversation thread created (ID: {self.thread_id[:8]}...)")
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
            
    def demonstrate_calendar_reading(self):
        """Demonstrate calendar reading capabilities."""
        print("\n" + "="*60)
        print("📅 DEMONSTRATION: Calendar Reading Capabilities")
        print("="*60)
        
        test_queries = [
            "What does my schedule look like for the next 3 days?",
            "Show me my meetings for today",
            "Do I have any conflicts between 2 PM and 4 PM tomorrow?",
            "What's on my calendar next week?",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n[Test {i}/4] 🔵 User Query:")
            print(f"         {query}")
            
            response = self.agent.process_message(self.thread_id, query)
            
            if response["status"] == "success":
                print(f"🤖 Agent Response:")
                print(f"         {response['message'][:200]}...")
            else:
                print(f"❌ Error: {response['message']}")
                
            time.sleep(2)  # Pause for demo effect
            
    def demonstrate_meeting_creation(self):
        """Demonstrate meeting creation capabilities."""
        print("\n" + "="*60)
        print("📝 DEMONSTRATION: Meeting Creation Capabilities")
        print("="*60)
        
        # Calculate tomorrow's date for demo
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        test_queries = [
            f"Book a 1-hour team standup meeting tomorrow at 9 AM with john@example.com and jane@example.com",
            f"Schedule a 30-minute client call for {tomorrow} at 2:30 PM with sarah.client@company.com, title 'Project Review'",
            "Create a 2-hour workshop next Friday from 10 AM to 12 PM, title 'Azure AI Training'",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n[Test {i}/3] 🔵 User Query:")
            print(f"         {query}")
            
            response = self.agent.process_message(self.thread_id, query)
            
            if response["status"] == "success":
                print(f"🤖 Agent Response:")
                print(f"         {response['message'][:200]}...")
            else:
                print(f"❌ Error: {response['message']}")
                
            time.sleep(2)  # Pause for demo effect
            
    def demonstrate_complex_scenarios(self):
        """Demonstrate complex scenario handling."""
        print("\n" + "="*60)
        print("🎯 DEMONSTRATION: Complex Scenario Handling")
        print("="*60)
        
        complex_queries = [
            "Find a 2-hour slot next week when I'm free to meet with the development team",
            "Check if I can reschedule my Monday 3 PM meeting to Tuesday same time",
            "What's the best time to schedule a meeting with someone in the New York timezone?",
        ]
        
        for i, query in enumerate(complex_queries, 1):
            print(f"\n[Test {i}/3] 🔵 Complex Query:")
            print(f"         {query}")
            
            response = self.agent.process_message(self.thread_id, query)
            
            if response["status"] == "success":
                print(f"🤖 Agent Response:")
                print(f"         {response['message'][:200]}...")
            else:
                print(f"❌ Error: {response['message']}")
                
            time.sleep(2)  # Pause for demo effect
            
    def demonstrate_error_handling(self):
        """Demonstrate error handling capabilities."""
        print("\n" + "="*60)
        print("⚠️  DEMONSTRATION: Error Handling & Recovery")
        print("="*60)
        
        error_scenarios = [
            "Book a meeting for yesterday at 3 PM",  # Past date
            "Schedule a meeting with invalid@email",  # Invalid email
            "Create a meeting without specifying any details",  # Missing details
            "Show me meetings for the 32nd of this month",  # Invalid date
        ]
        
        for i, query in enumerate(error_scenarios, 1):
            print(f"\n[Test {i}/4] 🔵 Error Scenario:")
            print(f"         {query}")
            
            response = self.agent.process_message(self.thread_id, query)
            
            print(f"🤖 Agent Handling:")
            if response["status"] == "success":
                print(f"         ✅ Graceful handling: {response['message'][:150]}...")
            else:
                print(f"         ⚠️  Error captured: {response['message']}")
                
            time.sleep(2)  # Pause for demo effect
            
    def show_monitoring_capabilities(self):
        """Show monitoring and logging capabilities."""
        print("\n" + "="*60)
        print("📊 DEMONSTRATION: Monitoring & Logging Capabilities")
        print("="*60)
        
        print("\n🔍 Log Files Generated:")
        
        log_files = [
            "calendar_agent.log",
            "agent_operations.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                print(f"   ✅ {log_file} ({size} bytes)")
                
                # Show last few lines
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print(f"      Last entry: {lines[-1].strip()}")
                except:
                    pass
            else:
                print(f"   ⚠️  {log_file} (not found)")
                
        print("\n📈 Key Metrics Tracked:")
        print("   • API call success/failure rates")
        print("   • Response times")
        print("   • Error types and frequencies")
        print("   • User interaction patterns")
        print("   • Tool usage statistics")
        
    def run_full_demo(self):
        """Run the complete demonstration."""
        print("🚀 Azure AI Foundry Calendar Agent - Client Demonstration")
        print("🕒 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("\n" + "="*60)
        
        if not self.setup_demo():
            print("❌ Demo setup failed. Exiting.")
            return
            
        try:
            # Run all demo sections
            self.demonstrate_calendar_reading()
            self.demonstrate_meeting_creation()
            self.demonstrate_complex_scenarios()
            self.demonstrate_error_handling()
            self.show_monitoring_capabilities()
            
            print("\n" + "="*60)
            print("✅ DEMONSTRATION COMPLETE")
            print("="*60)
            print("\n🎯 Key Takeaways:")
            print("   • Production-ready Azure AI Foundry agent integration")
            print("   • Robust Microsoft Graph API integration")
            print("   • Comprehensive error handling and logging")
            print("   • Scalable architecture for enterprise deployment")
            print("   • Full monitoring and observability")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Demo interrupted by user.")
        except Exception as e:
            print(f"\n\n❌ Demo failed with error: {e}")

def main():
    """Main entry point for the demo."""
    demo = ClientDemo()
    demo.run_full_demo()

if __name__ == "__main__":
    main()
