"""
Improved Microsoft Graph tools (APP-ONLY, client credentials).
- Uses ClientSecretCredential locally/by default
- Optional: Managed Identity in Azure (set USE_MANAGED_IDENTITY=true)
- IMPORTANT: App-only means NO '/me' endpoints; always use '/users/{UPN|id}'.

Requires:
  pip install azure-identity httpx python-dotenv
"""

import os
import json
import base64
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from azure.identity import ClientSecretCredential, ManagedIdentityCredential

# --- Logging setup ---
file_handler = logging.FileHandler("calendar_agent.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# --- Env ---
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

GRAPH_SCOPE_DEFAULT = "https://graph.microsoft.com/.default"
USE_MI = os.getenv("USE_MANAGED_IDENTITY", "false").lower() in ("1", "true", "yes")

# Required for client secret mode
REQUIRED_ENV_VARS = ["GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "DEFAULT_USER_UPN"]
if not USE_MI:
    REQUIRED_ENV_VARS.append("GRAPH_CLIENT_SECRET")

missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
if missing:
    raise ValueError(f"Missing required environment variables: {missing}")

# --- Validation helpers (prints) ---

REQUIRED_APP_ROLES = ["Calendars.ReadWrite", "User.Read.All"]
OPTIONAL_APP_ROLES = ["MailboxSettings.Read"]

_TOKEN_CACHE: Dict[str, Any] = {"token": None, "claims": None}

def _mask(s: Optional[str], show: int = 4) -> str:
    if not s:
        return "<empty>"
    if len(s) <= show * 2:
        return "*" * len(s)
    return f"{s[:show]}…{s[-show:]}"

def _b64url_json(part: str) -> Dict[str, Any]:
    pad = '=' * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(part + pad).decode("utf-8"))

def _decode_jwt(token: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, _ = token.split(".")
        payload = _b64url_json(payload_b64)
        return payload
    except Exception:
        return {}

def _print_config_once(payload: Dict[str, Any]) -> None:
    """Pretty-print identity, env, and roles (once per process)."""
    tenant = os.environ.get("GRAPH_TENANT_ID")
    client = os.environ.get("GRAPH_CLIENT_ID")
    use_mi = "Managed Identity" if USE_MI else "Client Secret"
    upn = os.environ.get("DEFAULT_USER_UPN", "")

    aud = payload.get("aud")
    appid = payload.get("appid")
    tid = payload.get("tid")
    roles = payload.get("roles", [])
    exp = payload.get("exp")

    print("\n=== GRAPH APP-ONLY VALIDATION ===")
    print(f"🔐 Auth mode            : {use_mi}")
    print(f"🏢 Tenant (env)         : {tenant}")
    print(f"👤 Client ID (env)      : {client}")
    if not USE_MI:
        print(f"🔏 Client Secret (env)  : {_mask(os.environ.get('GRAPH_CLIENT_SECRET'))}")
    print(f"📧 Target mailbox (env) : {upn}")
    print("— Token claims —")
    print(f"  • aud   : {aud}")
    print(f"  • tid   : {tid}")
    print(f"  • appid : {appid}")
    
    # Debug: Show ALL claims in the token
    print(f"  • ALL CLAIMS: {list(payload.keys())}")
    
    if isinstance(roles, list):
        print(f"  • roles : {', '.join(roles) if roles else '<none>'}")
    else:
        print(f"  • roles : {roles if roles is not None else '<NOT_PRESENT>'}")
    if exp:
        print(f"  • exp   : {datetime.fromtimestamp(int(exp), tz=timezone.utc)} (UTC)")

    # Role check
    missing_roles = [r for r in REQUIRED_APP_ROLES if r not in (roles or [])]
    if missing_roles:
        print(f"⚠️  Missing required app roles in token: {', '.join(missing_roles)}")
    else:
        print("✅ Required roles present in token")

    optional_missing = [r for r in OPTIONAL_APP_ROLES if r not in (roles or [])]
    if optional_missing:
        print(f"ℹ️  Optional roles not present: {', '.join(optional_missing)}")
    print("=================================\n")

def _tz() -> str:
    return os.getenv("DEFAULT_TZ", "UTC")

def _default_user() -> str:
    return os.getenv("DEFAULT_USER_UPN", "").strip()

def _validate_iso_datetime(date_str: str) -> bool:
    try:
        datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return True
    except (ValueError, TypeError):
        return False

def _get_app_token() -> str:
    """Acquire an app-only Graph token; print identity/roles the first time."""
    if _TOKEN_CACHE["token"]:
        return _TOKEN_CACHE["token"]

    if USE_MI:
        cred = ManagedIdentityCredential()
    else:
        cred = ClientSecretCredential(
            tenant_id=os.environ["GRAPH_TENANT_ID"],
            client_id=os.environ["GRAPH_CLIENT_ID"],
            client_secret=os.environ["GRAPH_CLIENT_SECRET"],
        )
    
    print(f"Requesting token with scope: {GRAPH_SCOPE_DEFAULT}")
    print(f"Tenant ID: {os.environ['GRAPH_TENANT_ID']}")
    print(f"Client ID: {os.environ['GRAPH_CLIENT_ID']}")
    
    token_response = cred.get_token(GRAPH_SCOPE_DEFAULT)
    token = token_response.token

    # Decode and print once
    claims = _decode_jwt(token) or {}
    _print_config_once(claims)

    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["claims"] = claims
    return token

# ---------------------- Public API ---------------------- #

def read_schedule(
    user_upn: Optional[str] = None,
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
    timezone_name: Optional[str] = None,
    select: Optional[List[str]] = None,
    top: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Returns events in [start_iso, end_iso] for the user's default calendar.
    App-only permission: always targets /users/{UPN}/calendarView (never /me).
    """
    logger.debug(f"Reading schedule for user: {user_upn or 'default'}")
    try:
        user = (user_upn or _default_user())
        if not user:
            raise ValueError("user_upn is required")

        now_utc = datetime.now(timezone.utc)
        if not start_iso or not end_iso:
            start_iso = now_utc.isoformat()
            end_iso = (now_utc + timedelta(days=7)).isoformat()

        if not (_validate_iso_datetime(start_iso) and _validate_iso_datetime(end_iso)):
            raise ValueError("Invalid ISO datetime format for start_iso or end_iso")

        if top is not None and (not isinstance(top, int) or top <= 0 or top > 1000):
            raise ValueError("top must be a positive integer <= 1000")

        tz = timezone_name or _tz()
        return asyncio.run(_read_schedule_async(user, start_iso, end_iso, tz, select, top))

    except ValueError as e:
        logger.error(f"Validation error in read_schedule: {e}")
        return {"error": "validation_error", "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in read_schedule: {e}")
        return {"error": "unexpected_error", "message": "An unexpected error occurred"}

async def _read_schedule_async(
    user: str,
    start_iso: str,
    end_iso: str,
    tz: str,
    select: Optional[List[str]],
    top: Optional[int],
) -> Dict[str, Any]:
    try:
        base = f"https://graph.microsoft.com/v1.0/users/{user}/calendarView"
        
        # Fix datetime formatting - ensure proper ISO format for Graph API
        # Graph API expects datetime in format: 2025-09-04T00:00:00.000Z or 2025-09-04T00:00:00+08:00
        from datetime import datetime
        
        # Parse and reformat the datetime strings to ensure correct format
        try:
            start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
            
            # Format as UTC ISO strings which Graph API prefers
            start_utc = start_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            end_utc = end_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
        except Exception as dt_error:
            logger.error(f"Datetime parsing error: {dt_error}")
            return {"error": "datetime_parsing_error", "message": f"Invalid datetime format: {dt_error}"}
        
        url = f"{base}?startDateTime={start_utc}&endDateTime={end_utc}"

        if select:
            allowed = ["id", "subject", "start", "end", "location", "attendees", "organizer", "bodyPreview"]
            invalid = [f for f in select if f not in allowed]
            if invalid:
                raise ValueError(f"Invalid select fields: {invalid}")
            url += f"&$select={','.join(select)}"
        else:
            # Include organizer information by default
            url += "&$select=id,subject,start,end,location,organizer"

        if top:
            url += f"&$top={int(top)}"
        else:
            # Limit to 10 events by default to reduce load
            url += "&$top=10"

        # Print the exact call being made
        print(f"API Call: GET {url}")
        print(f"Timezone: {tz}")

        import httpx
        access_token = _get_app_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": f'outlook.timezone="{tz}"',
        }

        async with httpx.AsyncClient(timeout=30.0) as http_client:  # Add timeout
            resp = await http_client.get(url, headers=headers)
            
            if resp.status_code == 200:
                data = resp.json()
                logger.debug(f"Retrieved {len(data.get('value', []))} events")
                return data

            # Enhanced error handling with specific Graph API codes
            logger.error(f"HTTP {resp.status_code}: {resp.text}")
            
            # Don't spam console with common format errors
            if resp.status_code != 400:
                print(f"ERROR: HTTP {resp.status_code}: {resp.text}")
            
            if resp.status_code == 429:  # Too Many Requests
                retry_after = resp.headers.get('Retry-After', 'unknown')
                return {"error": "rate_limit_exceeded", "message": f"Graph API rate limit exceeded. Retry after: {retry_after} seconds"}
            if resp.status_code == 403:
                return {"error": "permission_denied", "message": "App lacks required Application permissions."}
            if resp.status_code == 401:
                return {"error": "authentication_failed", "message": "Authentication failed. Check credentials."}
            if resp.status_code == 404:
                return {"error": "user_not_found", "message": f"User {user} not found."}
            if resp.status_code == 503:  # Service Unavailable
                return {"error": "service_unavailable", "message": "Graph API service temporarily unavailable"}
            return {"error": "graph_api_error", "message": f"Graph API error {resp.status_code}: {resp.text}"}

    except Exception as e:
        logger.error(f"Unexpected error in calendar reading: {e}")
        return {"error": "unexpected_error", "message": "Failed to read calendar"}

def create_meeting(
    subject: str,
    start_iso: str,
    end_iso: str,
    user_upn: Optional[str] = None,
    timezone_name: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    body_html: Optional[str] = None,
    location: Optional[str] = None,
    allow_new_time_proposals: bool = True,
    is_online_meeting: bool = True,
) -> Dict[str, Any]:
    """
    Creates an event on the user's default calendar (app-only).
    """
    logger.debug(f"Creating meeting '{subject}' for user: {user_upn or 'default'}")
    try:
        user = (user_upn or _default_user())
        if not user:
            raise ValueError("user_upn is required")

        if not subject or not subject.strip():
            raise ValueError("subject is required and cannot be empty")
        if not start_iso or not end_iso:
            raise ValueError("start_iso and end_iso are required")
        if not (_validate_iso_datetime(start_iso) and _validate_iso_datetime(end_iso)):
            raise ValueError("Invalid ISO datetime format for start_iso or end_iso")

        start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        if start_dt >= end_dt:
            raise ValueError("start_iso must be before end_iso")

        if attendees:
            import re
            pat = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            bad = [a for a in attendees if not re.match(pat, a)]
            if bad:
                raise ValueError(f"Invalid email addresses: {bad}")

        tz = timezone_name or _tz()
        return asyncio.run(
            _create_meeting_async(
                user,
                subject,
                start_iso,
                end_iso,
                tz,
                attendees,
                body_html,
                location,
                allow_new_time_proposals,
                is_online_meeting,
            )
        )

    except ValueError as e:
        logger.error(f"Validation error in create_meeting: {e}")
        return {"error": "validation_error", "message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in create_meeting: {e}")
        return {"error": "unexpected_error", "message": "An unexpected error occurred"}

async def _create_meeting_async(
    user: str,
    subject: str,
    start_iso: str,
    end_iso: str,
    tz: str,
    attendees: Optional[List[str]],
    body_html: Optional[str],
    location: Optional[str],
    allow_new_time_proposals: bool,
    is_online_meeting: bool,
) -> Dict[str, Any]:
    try:
        event: Dict[str, Any] = {
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
            event["attendees"] = [{"emailAddress": {"address": a}, "type": "required"} for a in attendees]
        if is_online_meeting:
            event["isOnlineMeeting"] = True
            event["onlineMeetingProvider"] = "teamsForBusiness"

        url = f"https://graph.microsoft.com/v1.0/users/{user}/events"
        print(f"API Call: POST {url}")
        print(f"Meeting Subject: {subject}")

        import httpx
        access_token = _get_app_token()
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient() as http_client:
            resp = await http_client.post(url, headers=headers, json=event)
            if resp.status_code == 201:
                created = resp.json()
                print(f"Event created successfully: {created.get('id')}")
                return {
                    "status": "created",
                    "eventId": created.get("id"),
                    "webLink": created.get("webLink"),
                    "subject": subject,
                }

            logger.error(f"HTTP {resp.status_code}: {resp.text}")
            print(f"HTTP Error {resp.status_code}: {resp.text}")
            if resp.status_code == 403:
                return {"error": "permission_denied", "message": "App lacks Calendars.ReadWrite (Application)."}
            if resp.status_code == 401:
                return {"error": "authentication_failed", "message": "Authentication failed. Check credentials."}
            if resp.status_code == 404:
                return {"error": "user_not_found", "message": f"User {user} not found."}
            if resp.status_code == 400:
                return {"error": "bad_request", "message": "Invalid meeting parameters."}
            return {"error": "graph_api_error", "message": f"Graph API error {resp.status_code}: {resp.text}"}

    except Exception as e:
        logger.error(f"Unexpected error in meeting creation: {e}")
        print(f"Error in meeting creation: {e}")
        return {"error": "unexpected_error", "message": "Failed to create meeting"}
