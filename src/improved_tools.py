"""
Improved Microsoft Graph tools with proper error handling, logging, and security.
"""
import os
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from kiota_abstractions.api_error import APIError

# Configure logging - detailed logs to file, minimal to console
file_handler = logging.FileHandler('calendar_agent.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)  # Only errors to console
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Security: Validate required environment variables
REQUIRED_ENV_VARS = [
    "GRAPH_TENANT_ID",
    "GRAPH_CLIENT_ID", 
    "GRAPH_CLIENT_SECRET",
    "DEFAULT_USER_UPN"
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {missing_vars}")

def graph_client() -> GraphServiceClient:
    """Create and return a Graph client with proper error handling."""
    try:
        cred = ClientSecretCredential(
            tenant_id=os.environ["GRAPH_TENANT_ID"],
            client_id=os.environ["GRAPH_CLIENT_ID"],
            client_secret=os.environ["GRAPH_CLIENT_SECRET"],
        )
        return GraphServiceClient(credentials=cred, scopes=["https://graph.microsoft.com/.default"])
    except Exception as e:
        logger.error(f"Failed to create Graph client: {e}")
        raise

# Remove sensitive debug prints - use logging instead
logger.debug(f"Graph client configured for tenant: {os.environ.get('GRAPH_TENANT_ID')[:8]}...")

def _tz() -> str:
    """Get default timezone."""
    return os.getenv("DEFAULT_TZ", "UTC")

def _default_user() -> str:
    """Get default user UPN."""
    return os.getenv("DEFAULT_USER_UPN")

def _validate_iso_datetime(date_str: str) -> bool:
    """Validate ISO 8601 datetime format."""
    try:
        datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return True
    except (ValueError, TypeError):
        return False

def read_schedule(
    user_upn: Optional[str] = None,
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
    timezone_name: Optional[str] = None,
    select: Optional[List[str]] = None,
    top: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Returns events in [start_iso, end_iso] for user's default calendar.
    If start/end missing, returns next 7 days from now.
    
    Args:
        user_upn: User principal name (email)
        start_iso: Start datetime in ISO format
        end_iso: End datetime in ISO format
        timezone_name: Timezone name
        select: Fields to select
        top: Maximum number of events to return
        
    Returns:
        Dict containing calendar events or error information
    """
    logger.debug(f"Reading schedule for user: {user_upn or 'default'}")
    
    try:
        user = user_upn or _default_user()
        if not user:
            raise ValueError("user_upn is required")

        # Validate and set default date range
        now_utc = datetime.now(timezone.utc)
        if not start_iso or not end_iso:
            start_iso = now_utc.isoformat()
            end_iso = (now_utc + timedelta(days=7)).isoformat()
        
        # Validate datetime formats
        if not (_validate_iso_datetime(start_iso) and _validate_iso_datetime(end_iso)):
            raise ValueError("Invalid ISO datetime format for start_iso or end_iso")

        # Validate top parameter
        if top is not None and (not isinstance(top, int) or top <= 0 or top > 1000):
            raise ValueError("top parameter must be a positive integer <= 1000")

        tz = timezone_name or _tz()
        client = graph_client()

        return asyncio.run(_read_schedule_async(client, user, start_iso, end_iso, tz, select, top))
        
    except ValueError as e:
        logger.error(f"Validation error in read_schedule: {e}")
        return {"error": "validation_error", "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in read_schedule: {e}")
        return {"error": "unexpected_error", "message": "An unexpected error occurred"}

async def _read_schedule_async(
    client: GraphServiceClient,
    user: str,
    start_iso: str,
    end_iso: str,
    tz: str,
    select: Optional[List[str]],
    top: Optional[int]
) -> Dict[str, Any]:
    """Async implementation of calendar reading."""
    try:
        # Build URL with proper query parameters
        base = f"https://graph.microsoft.com/v1.0/users/{user}/calendarView"
        url = f"{base}?startDateTime={start_iso}&endDateTime={end_iso}"
        
        if select:
            # Validate select fields
            allowed_fields = ["id", "subject", "start", "end", "location", "attendees", "organizer", "bodyPreview"]
            invalid_fields = [field for field in select if field not in allowed_fields]
            if invalid_fields:
                raise ValueError(f"Invalid select fields: {invalid_fields}")
            url += f"&$select={','.join(select)}"
            
        if top:
            url += f"&$top={int(top)}"

        req = client.users.by_user_id(user).calendar_view.with_url(url)
        request_info = req.to_get_request_information()
        request_info.headers.add("Prefer", f'outlook.timezone="{tz}"')

        result = await client.request_adapter.send_async(request_info, dict, None)
        
        logger.debug(f"Successfully retrieved {len(result.get('value', []))} events")
        return result
        
    except APIError as ae:
        status = getattr(ae, "response_status_code", None)
        detail = getattr(ae, "message", "")
        
        logger.error(f"Graph API error {status}: {detail}")
        
        # Handle specific error scenarios
        if status == 401:
            return {"error": "authentication_failed", "message": "Authentication failed. Check credentials."}
        elif status == 403:
            return {"error": "permission_denied", "message": "Insufficient permissions to read calendar."}
        elif status == 404:
            return {"error": "user_not_found", "message": f"User {user} not found."}
        else:
            return {"error": "graph_api_error", "message": f"Graph API error {status}: {detail}"}
            
    except Exception as e:
        logger.error(f"Unexpected error in calendar reading: {e}")
        return {"error": "unexpected_error", "message": "Failed to read calendar"}

def create_meeting(
    user_upn: Optional[str],
    subject: str,
    start_iso: str,
    end_iso: str,
    timezone_name: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    body_html: Optional[str] = None,
    location: Optional[str] = None,
    allow_new_time_proposals: bool = True,
    is_online_meeting: bool = True,
) -> Dict[str, Any]:
    """
    Creates an event on user's default calendar for the given window.
    
    Args:
        user_upn: User principal name
        subject: Meeting subject
        start_iso: Start datetime in ISO format
        end_iso: End datetime in ISO format
        timezone_name: Timezone name
        attendees: List of attendee email addresses
        body_html: Meeting body content
        location: Meeting location
        allow_new_time_proposals: Allow time proposals
        is_online_meeting: Create as online meeting
        
    Returns:
        Dict containing meeting creation result or error information
    """
    logger.debug(f"Creating meeting '{subject}' for user: {user_upn or 'default'}")
    
    try:
        user = user_upn or _default_user()
        if not user:
            raise ValueError("user_upn is required")
            
        # Validate required parameters
        if not subject or not subject.strip():
            raise ValueError("subject is required and cannot be empty")
            
        if not start_iso or not end_iso:
            raise ValueError("start_iso and end_iso are required")
            
        # Validate datetime formats
        if not (_validate_iso_datetime(start_iso) and _validate_iso_datetime(end_iso)):
            raise ValueError("Invalid ISO datetime format for start_iso or end_iso")
            
        # Validate start is before end
        start_dt = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_iso.replace('Z', '+00:00'))
        if start_dt >= end_dt:
            raise ValueError("start_iso must be before end_iso")
            
        # Validate attendees email format (basic validation)
        if attendees:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            invalid_emails = [email for email in attendees if not re.match(email_pattern, email)]
            if invalid_emails:
                raise ValueError(f"Invalid email addresses: {invalid_emails}")

        tz = timezone_name or _tz()
        client = graph_client()

        return asyncio.run(_create_meeting_async(
            client, user, subject, start_iso, end_iso, tz, 
            attendees, body_html, location, allow_new_time_proposals, is_online_meeting
        ))
        
    except ValueError as e:
        logger.error(f"Validation error in create_meeting: {e}")
        return {"error": "validation_error", "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in create_meeting: {e}")
        return {"error": "unexpected_error", "message": "An unexpected error occurred"}

async def _create_meeting_async(
    client: GraphServiceClient,
    user: str,
    subject: str,
    start_iso: str,
    end_iso: str,
    tz: str,
    attendees: Optional[List[str]],
    body_html: Optional[str],
    location: Optional[str],
    allow_new_time_proposals: bool,
    is_online_meeting: bool
) -> Dict[str, Any]:
    """Async implementation of meeting creation."""
    try:
        # Build event object
        event = {
            "subject": subject,
            "start": {"dateTime": start_iso, "timeZone": tz},
            "end": {"dateTime": end_iso, "timeZone": tz},
            "allowNewTimeProposals": allow_new_time_proposals,
        }
        
        if body_html:
            event["body"] = {"contentType": "HTML", "content": body_html}
            
        if location:
            event["location"] = {"displayName": location}
            
        if attendees:
            event["attendees"] = [
                {"emailAddress": {"address": email}, "type": "required"} 
                for email in attendees
            ]
            
        if is_online_meeting:
            event["isOnlineMeeting"] = True
            event["onlineMeetingProvider"] = "teamsForBusiness"

        created = await client.users.by_user_id(user).events.post(body=event)
        
        # Extract event details safely
        event_id = getattr(created, "id", None) or (created.get("id") if isinstance(created, dict) else None)
        web_link = getattr(created, "web_link", None) or getattr(created, "webLink", None)
        
        logger.debug(f"Successfully created meeting with ID: {event_id}")
        return {
            "status": "created", 
            "eventId": event_id, 
            "webLink": web_link,
            "subject": subject
        }
        
    except APIError as ae:
        status = getattr(ae, "response_status_code", None)
        detail = getattr(ae, "message", "")
        
        logger.error(f"Graph API error {status}: {detail}")
        
        # Handle specific error scenarios
        if status == 401:
            return {"error": "authentication_failed", "message": "Authentication failed. Check credentials."}
        elif status == 403:
            return {
                "error": "permission_denied", 
                "message": "Insufficient permissions. Ensure Calendars.ReadWrite permission is granted."
            }
        elif status == 404:
            return {"error": "user_not_found", "message": f"User {user} not found."}
        elif status == 400:
            return {"error": "bad_request", "message": "Invalid meeting parameters provided."}
        else:
            return {"error": "graph_api_error", "message": f"Graph API error {status}: {detail}"}
            
    except Exception as e:
        logger.error(f"Unexpected error in meeting creation: {e}")
        return {"error": "unexpected_error", "message": "Failed to create meeting"}
