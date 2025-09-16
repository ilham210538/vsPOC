#!/usr/bin/env python3
"""
Simple CLI wrapper for the Calendar Agent that can be called from Node.js
This replaces interactive_chat.py for web deployment
"""
import sys
import json
import argparse
import logging
import io
import contextlib
from enhanced_agent import CalendarAgent

# Suppress verbose logging for web deployment
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

@contextlib.contextmanager
def suppress_stdout():
    """Context manager to suppress stdout during agent processing"""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = old_stdout

def process_message(message, thread_id=None):
    """Process a single message and return response - create fresh agent each time"""
    try:
        # Create fresh agent for each request to avoid connection issues
        agent = CalendarAgent()
        
        # Use the agent within proper context and suppress debug output
        with agent.project:
            # Create agent instance
            agent_id = agent.create_agent()
            
            # Create or use thread
            if thread_id:
                current_thread_id = thread_id
            else:
                current_thread_id = agent.create_conversation_thread()
            
            # Process the message with suppressed output
            with suppress_stdout():
                response = agent.process_message(current_thread_id, message)
            
            # Clean up
            agent.delete_agent()
            
            return {
                "status": response["status"],
                "message": response["message"],
                "thread_id": current_thread_id,
                "timestamp": response.get("timestamp", "")
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing message: {str(e)}",
            "thread_id": thread_id,
            "error_details": str(e)
        }

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Calendar Agent CLI Wrapper')
    parser.add_argument('--message', required=True, help='Message to send to agent')
    parser.add_argument('--thread', help='Thread ID to use (optional)')
    parser.add_argument('--json', action='store_true', help='Output JSON response')
    
    args = parser.parse_args()
    
    try:
        # Process the message
        result = process_message(args.message, args.thread)
        
        if args.json:
            # Output JSON for Node.js consumption
            print(json.dumps(result))
        else:
            # Human-readable output
            if result["status"] == "success":
                print(f"Agent: {result['message']}")
            else:
                print(f"Error: {result['message']}")
                sys.exit(1)
                
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"CLI Error: {str(e)}",
            "thread_id": None
        }
        
        if args.json:
            print(json.dumps(error_result))
        else:
            print(f"CLI Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
