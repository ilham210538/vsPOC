#!/usr/bin/env python3
"""
Persistent Agent Session Manager for Calendar Agent Web Interface
Maintains agent and thread sessions across multiple messages
"""
import sys
import json
import argparse
import logging
import io
import contextlib
import atexit
import os
from datetime import datetime
from enhanced_agent import CalendarAgent

# Suppress verbose logging for web deployment
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

class RotatingFileLogger:
    """Simple rotating file logger that keeps only the last N lines"""
    
    def __init__(self, log_dir="debugging_logs", max_lines=30):
        self.log_dir = log_dir
        self.max_lines = max_lines
        
        # Create log directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def log(self, filename, message):
        log_file = os.path.join(self.log_dir, f"{filename}.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        try:
            # Read existing lines
            existing_lines = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    existing_lines = [line.strip() for line in f.readlines() if line.strip()]
            
            # Add session separator for new actions
            if 'Initializing' in message or 'Starting cleanup' in message:
                existing_lines.append('')  # Add spacing
                existing_lines.append('-' * 50)
            
            # Add new line
            existing_lines.append(log_entry)
            
            # Keep only last max_lines
            if len(existing_lines) > self.max_lines:
                existing_lines = existing_lines[-self.max_lines:]
            
            # Write back with clean formatting
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(existing_lines) + '\n')
                
        except Exception as e:
            print(f"Failed to write to log {filename}: {e}", file=sys.stderr)
    
    def agent(self, message):
        self.log('agent', f"AGENT: {message}")

# Initialize logger
file_logger = RotatingFileLogger()

class AgentSession:
    """Manages a persistent agent session"""
    
    def __init__(self):
        self.agent = None
        self.agent_id = None
        self.thread_id = None
        self.project_context = None
        
    def initialize(self):
        """Initialize the agent and create persistent session"""
        try:
            if self.agent is None:
                file_logger.agent('Initializing new agent session')
                self.agent = CalendarAgent()
                self.project_context = self.agent.project
                self.project_context.__enter__()
                
                # Create agent instance
                self.agent_id = self.agent.create_agent()
                file_logger.agent(f'Agent created with ID: {self.agent_id}')
                
                # Create conversation thread
                self.thread_id = self.agent.create_conversation_thread()
                file_logger.agent(f'Thread created with ID: {self.thread_id}')
                
                # DO NOT register cleanup on exit - we want persistent session
                # atexit.register(self.cleanup)  # REMOVED - this was causing cleanup after every message
                
                return True
        except Exception as e:
            file_logger.agent(f'ERROR: Failed to initialize agent session: {e}')
            print(f"Failed to initialize agent session: {e}", file=sys.stderr)
            return False
            
    def process_message(self, message):
        """Process message with existing agent and thread"""
        try:
            if not self.agent or not self.thread_id:
                if not self.initialize():
                    return {
                        "status": "error",
                        "message": "Failed to initialize agent session",
                        "thread_id": None
                    }
            
            file_logger.agent(f'Processing: "{message[:30]}..." (Agent: {self.agent_id})')
            
            # Suppress debug output for clean JSON
            with self._suppress_stdout():
                response = self.agent.process_message(self.thread_id, message)
            
            file_logger.agent(f'Processed successfully: {response["status"]}')
            
            return {
                "status": response["status"],
                "message": response["message"],
                "thread_id": self.thread_id,
                "timestamp": response.get("timestamp", ""),
                "tool_calls": response.get("tool_calls", [])
            }
            
        except Exception as e:
            file_logger.agent(f'ERROR: Error processing message: {str(e)}')
            return {
                "status": "error", 
                "message": f"Error processing message: {str(e)}",
                "thread_id": self.thread_id,
                "error_details": str(e)
            }
    
    def reset_session(self):
        """Reset the session - create new thread"""
        try:
            file_logger.agent('Resetting session - creating new thread')
            if self.agent and self.agent_id:
                # Create new thread but keep same agent
                self.thread_id = self.agent.create_conversation_thread()
                file_logger.agent(f'New thread created: {self.thread_id}, keeping same agent: {self.agent_id}')
                return {
                    "status": "success",
                    "message": "Session reset - new conversation started", 
                    "thread_id": self.thread_id
                }
            else:
                # Re-initialize everything
                file_logger.agent('Re-initializing entire session')
                self.cleanup()
                if self.initialize():
                    return {
                        "status": "success",
                        "message": "Session reset - new agent and conversation started",
                        "thread_id": self.thread_id
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to reset session"
                    }
        except Exception as e:
            file_logger.agent(f'ERROR: Error resetting session: {str(e)}')
            return {
                "status": "error",
                "message": f"Error resetting session: {str(e)}"
            }
    
    def cleanup(self):
        """Clean up agent resources"""
        try:
            file_logger.agent('Starting cleanup of agent resources')
            if self.agent and self.agent_id:
                self.agent.delete_agent()
                file_logger.agent(f'Agent {self.agent_id} deleted successfully')
            
            if self.project_context:
                self.project_context.__exit__(None, None, None)
                file_logger.agent('Project context closed')
                
            self.agent = None
            self.agent_id = None
            self.thread_id = None
            self.project_context = None
            
            file_logger.agent('Cleanup completed successfully')
            
        except Exception as e:
            file_logger.agent(f'ERROR: Error during cleanup: {e}')
            print(f"Error during cleanup: {e}", file=sys.stderr)
    
    @contextlib.contextmanager
    def _suppress_stdout(self):
        """Context manager to suppress stdout during agent processing"""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            yield
        finally:
            sys.stdout = old_stdout

# Global session instance
_session = AgentSession()

def main():
    """Main CLI interface for session management"""
    parser = argparse.ArgumentParser(description='Calendar Agent Session Manager')
    parser.add_argument('--action', choices=['message', 'reset', 'cleanup'], required=True, help='Action to perform')
    parser.add_argument('--message', help='Message to send to agent (for message action)')
    parser.add_argument('--json', action='store_true', default=True, help='Output JSON response')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'message':
            if not args.message:
                raise ValueError("Message is required for message action")
            result = _session.process_message(args.message)
            
        elif args.action == 'reset':
            result = _session.reset_session()
            
        elif args.action == 'cleanup':
            _session.cleanup()
            result = {"status": "success", "message": "Session cleaned up"}
        
        # Always output JSON for Node.js consumption
        print(json.dumps(result))
                
    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"Session Error: {str(e)}",
            "thread_id": _session.thread_id
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()
