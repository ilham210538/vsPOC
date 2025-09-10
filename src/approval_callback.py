"""
Callback service to handle approval responses from Logic App.
This creates the webhook endpoint that your Logic App will call back to.
"""
import os
import json
import logging
from typing import Dict, Any
from datetime import datetime, timezone
import asyncio
from threading import Thread
import time
import queue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global queue for real-time notifications
notification_queue = queue.Queue()

# Global storage for persistent notifications across instances
global_recent_notifications = []

class ApprovalCallbackService:
    """
    Service to handle approval callbacks from Logic App and notify the agent/user.
    This runs as a simple HTTP server to receive callbacks.
    """
    
    def __init__(self):
        self.pending_approvals = {}  # Store pending approval requests
        self.approval_responses = {}  # Store completed approval responses
        self.callback_base_url = os.getenv("CALLBACK_BASE_URL", "http://localhost:5000")
        # Use global notification storage to share between instances
        global global_recent_notifications
        self.recent_notifications = global_recent_notifications
        self.notification_timeout = 300  # Keep notifications for 5 minutes
        
    def register_approval_request(
        self, 
        approval_id: str, 
        request_details: Dict[str, Any]
    ) -> str:
        """
        Register a new approval request and return the callback URL.
        
        Args:
            approval_id: Unique identifier for this approval request
            request_details: Details of what was requested for approval
            
        Returns:
            Callback URL for the Logic App to use
        """
        callback_url = f"{self.callback_base_url}/api/approval/callback/{approval_id}"
        
        self.pending_approvals[approval_id] = {
            "request_details": request_details,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "callback_url": callback_url
        }
        
        logger.info(f"Registered approval request {approval_id} with callback URL: {callback_url}")
        return callback_url
    
    def handle_approval_response(
        self,
        approval_id: str,
        status: str,  # "APPROVED" or "REJECTED" 
        selected_option: str,  # "Approve" or "Reject"
        message: str
    ) -> Dict[str, Any]:
        """
        Handle approval response from Logic App callback.
        
        Args:
            approval_id: The approval request ID
            status: APPROVED or REJECTED
            selected_option: Approve or Reject  
            message: Message from Logic App
            
        Returns:
            Processing result
        """
        try:
            if approval_id not in self.pending_approvals:
                return {
                    "error": f"Approval ID {approval_id} not found",
                    "status": "error"
                }
            
            # Update the approval record
            approval_data = self.pending_approvals[approval_id]
            approval_data.update({
                "status": status.lower(),
                "selected_option": selected_option,
                "logic_app_message": message,
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            
            # Move to completed responses
            self.approval_responses[approval_id] = approval_data
            del self.pending_approvals[approval_id]
            
            logger.info(f"Processed approval response for {approval_id}: {status}")
            
            # Here you could notify the user or trigger follow-up actions
            if status == "APPROVED":
                self._handle_approved_request(approval_id, approval_data)
            else:
                self._handle_rejected_request(approval_id, approval_data)
            
            return {
                "status": "success",
                "message": f"Approval {approval_id} processed: {status}",
                "approval_data": approval_data
            }
            
        except Exception as e:
            logger.error(f"Error handling approval response: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _handle_approved_request(self, approval_id: str, approval_data: Dict[str, Any]):
        """Handle approved requests - implement business logic here."""
        request_type = approval_data["request_details"].get("type")
        
        if request_type == "leave_request":
            # Add real-time notification
            notification_message = {
                "type": "approval_update",
                "approval_id": approval_id,
                "status": "APPROVED",
                "message": f"🎉 Great news! Your leave request has been APPROVED!\n\n"
                          f"📋 **Approval Details:**\n"
                          f"- **Request ID:** {approval_id}\n"
                          f"- **Status:** ✅ APPROVED\n"
                          f"- **Manager's Response:** {approval_data.get('logic_app_message', 'Approved')}\n"
                          f"- **Processed:** {approval_data.get('completed_at', 'Just now')}\n\n"
                          f"🗓️ Your leave has been added to the system. Enjoy your time off!",
                "details": approval_data
            }
            
            # Put notification in queue for real-time display
            notification_queue.put(notification_message)
            
            # Also store in persistent list with timestamp
            notification_with_time = {
                **notification_message,
                "timestamp": time.time()
            }
            global global_recent_notifications
            global_recent_notifications.append(notification_with_time)
            
            # Here you could:
            # - Update HR system
            # - Block calendar
            # - Send confirmation emails
            
        elif request_type == "meeting_request":
            logger.info(f"Meeting request {approval_id} approved - would create meeting")
            # Here you could:
            # - Create the actual meeting
            # - Send calendar invites
            # - Update project management systems
    
    def _handle_rejected_request(self, approval_id: str, approval_data: Dict[str, Any]):
        """Handle rejected requests."""
        
        # Add real-time notification
        notification_message = {
            "type": "approval_update", 
            "approval_id": approval_id,
            "status": "REJECTED",
            "message": f"❌ Your leave request has been rejected.\n\n"
                      f"📋 **Rejection Details:**\n"
                      f"- **Request ID:** {approval_id}\n"
                      f"- **Status:** ❌ REJECTED\n"
                      f"- **Manager's Response:** {approval_data.get('logic_app_message', 'Rejected')}\n"
                      f"- **Processed:** {approval_data.get('completed_at', 'Just now')}\n\n"
                      f"💬 You may want to discuss this with your manager for more details.",
            "details": approval_data
        }
        
        # Put notification in queue for real-time display
        notification_queue.put(notification_message)
        
        # Also store in persistent list with timestamp
        notification_with_time = {
            **notification_message,
            "timestamp": time.time()
        }
        global global_recent_notifications
        global_recent_notifications.append(notification_with_time)
        
        # Here you could:
        # - Send rejection notification to requester
        # - Log the rejection reason
        # - Update request tracking systems
    
    def get_approval_status(self, approval_id: str) -> Dict[str, Any]:
        """Get current status of an approval request."""
        # Check pending first
        if approval_id in self.pending_approvals:
            return {
                "status": "success",
                "approval_status": "pending",
                "data": self.pending_approvals[approval_id]
            }
        
        # Check completed
        if approval_id in self.approval_responses:
            return {
                "status": "success", 
                "approval_status": "completed",
                "data": self.approval_responses[approval_id]
            }
        
        return {
            "status": "error",
            "message": f"Approval ID {approval_id} not found"
        }
    
    def check_notifications(self) -> Dict[str, Any]:
        """Check for pending real-time notifications."""
        notifications = []
        current_time = time.time()
        
        # First, get any new notifications from queue
        while not notification_queue.empty():
            try:
                notification = notification_queue.get_nowait()
                notifications.append(notification)
            except queue.Empty:
                break
        
        # Also check recent persistent notifications (last 5 minutes)
        # Remove old notifications from global list
        global global_recent_notifications
        global_recent_notifications[:] = [
            notif for notif in global_recent_notifications 
            if current_time - notif.get("timestamp", 0) < self.notification_timeout
        ]
        
        # Add recent notifications that haven't been shown yet
        for notif in global_recent_notifications:
            # Remove timestamp before adding to notifications
            clean_notif = {k: v for k, v in notif.items() if k != "timestamp"}
            if clean_notif not in notifications:
                notifications.append(clean_notif)
        
        if notifications:
            return {
                "status": "success",
                "has_notifications": True,
                "notifications": notifications,
                "count": len(notifications)
            }
        else:
            return {
                "status": "success", 
                "has_notifications": False,
                "notifications": [],
                "count": 0
            }
    
    def clear_shown_notifications(self):
        """Clear all shown notifications to prevent duplicates."""
        global global_recent_notifications
        global_recent_notifications.clear()
        
        # Also clear the queue
        while not notification_queue.empty():
            try:
                notification_queue.get_nowait()
            except queue.Empty:
                break
    
    def wait_for_approval(self, approval_id: str, timeout_seconds: int = 300) -> Dict[str, Any]:
        """
        Wait for an approval decision (blocking call).
        Useful for interactive scenarios where you want to wait for the response.
        
        Args:
            approval_id: The approval request ID to wait for
            timeout_seconds: Maximum time to wait (default 5 minutes)
            
        Returns:
            Approval result or timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            if approval_id in self.approval_responses:
                return {
                    "status": "completed",
                    "data": self.approval_responses[approval_id]
                }
            
            time.sleep(2)  # Check every 2 seconds
        
        return {
            "status": "timeout",
            "message": f"Approval {approval_id} timed out after {timeout_seconds} seconds"
        }


# Global callback service instance
callback_service = ApprovalCallbackService()


def create_simple_callback_server():
    """
    Create a simple HTTP server to handle Logic App callbacks.
    This is a minimal implementation - for production use Flask/FastAPI.
    """
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse
    
    class CallbackHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                # Parse the URL to get approval_id (remove query parameters if any)
                clean_path = self.path.split('?')[0]  # Remove query parameters
                path_parts = clean_path.strip('/').split('/')
                
                if len(path_parts) >= 4 and path_parts[0] == 'api' and path_parts[1] == 'approval' and path_parts[2] == 'callback':
                    approval_id = path_parts[3]
                    
                    # Read the request body
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    
                    # Parse JSON payload from Logic App
                    try:
                        payload = json.loads(post_data.decode('utf-8'))
                        
                        # Extract fields based on your Logic App's callback format
                        status = payload.get('status')  # "APPROVED" or "REJECTED"
                        selected_option = payload.get('selectedOption')  # "Approve" or "Reject"
                        message = payload.get('message', '')
                        
                        # Process the approval response
                        result = callback_service.handle_approval_response(
                            approval_id, status, selected_option, message
                        )
                        
                        # Send response
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode('utf-8'))
                        
                        logger.info(f"✅ Approval processed: {approval_id} - {status}")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in callback: {e}")
                        self.send_error(400, f"Invalid JSON: {str(e)}")
                        
                else:
                    logger.error(f"Invalid callback URL format. Expected /api/approval/callback/{{id}}, got: {clean_path}")
                    logger.error(f"Path parts: {path_parts}, Length: {len(path_parts)}")
                    self.send_error(404, "Invalid callback URL format")
                    
            except Exception as e:
                logger.error(f"Error handling callback: {e}")
                self.send_error(500, f"Internal server error: {str(e)}")
        
        def log_message(self, format, *args):
            # Suppress default HTTP server logging
            pass
    
    # Start server on port 5000
    port = int(os.getenv('CALLBACK_PORT', 5000))
    server = HTTPServer(('localhost', port), CallbackHandler)
    
    logger.info(f"Starting callback server on http://localhost:{port}")
    logger.info("Callback URL format: http://localhost:{port}/api/approval/callback/{approval_id}")
    
    return server


def start_callback_server_background():
    """Start the callback server in a background thread."""
    def run_server():
        server = create_simple_callback_server()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down callback server")
            server.shutdown()
    
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    logger.info("Callback server started in background thread")
    return thread


if __name__ == "__main__":
    # Run the callback server directly
    server = create_simple_callback_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down callback server")
        server.shutdown()
