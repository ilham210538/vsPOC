"""
Simple Azure Logic App HTTP integration for Calendar Agent
Direct HTTP webhook approach - no Azure Management SDK needed
"""
import os
import json
import logging
import uuid
from typing import Dict, Any, Optional
import httpx

# Import callback service for approval tracking
try:
    from approval_callback import callback_service
except ImportError:
    callback_service = None

logger = logging.getLogger(__name__)

class SimpleLogicAppTool:
    """
    Simple Logic App integration via direct HTTP calls.
    This is the recommended approach for calling Logic Apps.
    """
    
    def __init__(self, logic_app_url: str):
        self.logic_app_url = logic_app_url
        
    async def invoke_logic_app(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the Logic App with the given payload via direct HTTP POST.
        
        Args:
            payload: JSON payload to send to the Logic App
            
        Returns:
            Response from the Logic App invocation
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.logic_app_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 202]:
                    logger.info("Successfully invoked Logic App via HTTP")
                    return {
                        "status": "success",
                        "status_code": response.status_code,
                        "response": response.json() if response.text else {"message": "Request accepted"}
                    }
                else:
                    logger.error(f"Logic App invocation failed: {response.status_code} - {response.text}")
                    return {
                        "status": "error",
                        "status_code": response.status_code,
                        "error": response.text
                    }
                    
        except Exception as e:
            logger.error(f"Error invoking Logic App: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


def create_send_approval_email_function(logic_app_tool: SimpleLogicAppTool):
    """
    Create a specialized function for sending approval emails via Logic App.
    This function will be used by the Azure AI Agent.
    """
    
    async def send_approval_email(
        to: str,
        subject: str,
        body_text: str,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an approval email using the Logic App.
        
        Args:
            to: Email address of the approver
            subject: Subject line for the approval email
            body_text: Plain text body of the email
            callback_url: Optional callback URL for receiving the approval decision
            
        Returns:
            Result of the Logic App invocation
        """
        try:
            # Prepare payload according to your Logic App schema
            payload = {
                "message": {
                    "to": to,
                    "subject": subject,
                    "bodyText": body_text
                }
            }
            
            # Add callback URL if provided
            if callback_url:
                payload["callbackUrl"] = callback_url
            
            # Call the async Logic App function
            result = await logic_app_tool.invoke_logic_app(payload)
            logger.info(f"Approval email result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in send_approval_email: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Set function metadata for the AI agent
    send_approval_email.__name__ = "send_approval_email"
    send_approval_email.__doc__ = """
    Send an approval email via Logic App for leave requests or meeting approvals.
    
    Use this function when a user requests approval for:
    - Leave/vacation requests
    - Meeting scheduling that requires manager approval
    - Any other approval workflow
    
    Parameters:
    - to: Email address of the person who should approve (manager, admin, etc.)
    - subject: Clear subject line describing what needs approval
    - body_text: Detailed plain text description of the request
    - callback_url: Optional URL to receive the approval decision
    
    The Logic App will send an email with Approve/Reject buttons to the specified recipient.
    """
    
    return send_approval_email


def create_leave_request_function(logic_app_tool: SimpleLogicAppTool):
    """
    Create a specialized function for leave requests that integrates with calendar checking.
    """
    
    async def request_leave_approval(
        leave_start_date: str,
        leave_end_date: str,
        leave_reason: str,
        manager_email: str,
        employee_name: str = None,
        employee_email: str = None,
        calendar_status: str = None,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request leave approval with automatic calendar conflict checking.
        
        Args:
            leave_start_date: Start date of leave (YYYY-MM-DD format)
            leave_end_date: End date of leave (YYYY-MM-DD format)
            leave_reason: Reason for leave request
            manager_email: Manager's email for approval
            employee_name: Name of employee requesting leave (optional, will get from env)
            employee_email: Email of employee requesting leave (optional, will get from env)
            calendar_status: Status of calendar conflicts (optional)
            callback_url: Optional callback URL for approval decision
            
        Returns:
            Result of the leave request submission
        """
        try:
            # Get user information from environment if not provided
            if not employee_name:
                import os
                # Get name from DEFAULT_USER_UPN email (e.g., "john.doe@company.com" -> "John Doe")
                user_upn = os.getenv('DEFAULT_USER_UPN', 'employee@company.com')
                email_prefix = user_upn.split('@')[0]
                # Convert "john.doe" or "john_doe" to "John Doe"
                name_parts = email_prefix.replace('.', ' ').replace('_', ' ').split()
                employee_name = ' '.join(word.capitalize() for word in name_parts)
            
            if not employee_email:
                import os
                employee_email = os.getenv('DEFAULT_USER_UPN', 'employee@company.com')
            
            # Generate unique approval ID for tracking
            approval_id = str(uuid.uuid4())
            
            # Register the approval request with callback service if available
            if not callback_url and callback_service:
                request_details = {
                    "type": "leave_request",
                    "employee_name": employee_name,
                    "employee_email": employee_email,
                    "leave_start_date": leave_start_date,
                    "leave_end_date": leave_end_date,
                    "leave_reason": leave_reason,
                    "manager_email": manager_email
                }
                callback_url = callback_service.register_approval_request(approval_id, request_details)
            
            # Format calendar status message
            if calendar_status:
                calendar_message = f"\nCalendar Status: {calendar_status}"
            else:
                calendar_message = "\nCalendar Status: Please verify calendar for any conflicts before approval."
            
            # Format the approval email content
            subject = f"Leave Request Approval: {employee_name} ({leave_start_date} to {leave_end_date})"
            
            body_text = f"""
Leave Request Details:

Employee: {employee_name} ({employee_email})
Leave Period: {leave_start_date} to {leave_end_date}
Reason: {leave_reason}{calendar_message}

Please review and approve or reject this leave request.
"""
            
            # Prepare payload for your Logic App
            payload = {
                "message": {
                    "to": manager_email,
                    "subject": subject,
                    "bodyText": body_text
                }
            }
            
            if callback_url:
                payload["callbackUrl"] = callback_url
            
            # Call the async Logic App function
            result = await logic_app_tool.invoke_logic_app(payload)
            logger.info(f"Leave approval result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in request_leave_approval: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Set function metadata
    request_leave_approval.__name__ = "request_leave_approval"
    request_leave_approval.__doc__ = """
    Submit a leave request for manager approval via Logic App.
    
    This function should be used when an employee wants to request time off.
    It will automatically format the approval email and send it to the manager.
    
    Before calling this function, consider:
    1. Checking the employee's calendar for conflicts using read_schedule()
    2. Verifying the leave dates are valid
    3. Ensuring all required information is provided
    
    Parameters:
    - leave_start_date: Start date in YYYY-MM-DD format
    - leave_end_date: End date in YYYY-MM-DD format  
    - leave_reason: Clear reason for the leave request
    - manager_email: Manager's email address for approval
    - employee_name: Full name of the employee
    - employee_email: Employee's email address
    - callback_url: Optional callback URL to receive approval decision
    """
    
    return request_leave_approval
