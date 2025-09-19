"""
FlexHR Leave API Integration Tool
Provides comprehensive leave management functionality including:
- Login (submitter/approver)
- Leave entitlement checking
- Leave submission and management
- Leave approval workflow

Based on FlexHR OpenAPI specification for Visual Solutions Sdn Bhd
"""

import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)

# FlexHR API Constants for Development/Testing
FLEXHR_BASE_URL = "https://dev.renecosystem.com/reneco_int/api"
DEV_CONSTANTS = {
    "devid": "990000862471854",
    "buid": "a33a4b19-ae4d-4dbf-b5b2-c6ae513a48e3",
    "appver": "10.2.1",
    "langid": "en-US",
    "tz": "8",
    "colastsync": "2017-11-15 19:45:12",
    "emplastsync": "2017-11-15 19:45:12", 
    "usrlastsync": "2017-11-15 19:45:12"
}

# Test credentials (for development only)
TEST_CREDENTIALS = {
    "submitter": {"login": "lee001", "pwd": "password1vs"},
    "approver": {"login": "lee003", "pwd": "password1vs"}
}

class FlexHRLeaveAPI:
    """FlexHR Leave API client for handling all leave-related operations."""
    
    def __init__(self):
        self.session_token = None
        self.current_devid = None
        self.current_user_type = None
        
    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to FlexHR API."""
        url = f"{FLEXHR_BASE_URL}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.debug(f"FlexHR API call successful: {endpoint}")
                    return {
                        "status": "success",
                        "data": result
                    }
                else:
                    logger.error(f"FlexHR API error: {response.status_code} - {response.text}")
                    return {
                        "status": "error",
                        "error": f"API returned status {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"FlexHR API request failed: {e}")
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}"
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in FlexHR format."""
        return datetime.now(timezone(timedelta(hours=8))).isoformat()
        
    def _format_date_for_flexhr(self, date_str: str) -> str:
        """Format date string for FlexHR API (YYYY-MM-DD HH:MM:SS+08:00)."""
        if not date_str:
            return ""
        
        # Handle various input formats
        try:
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                
            # Convert to UTC+8 timezone
            dt_utc8 = dt.astimezone(timezone(timedelta(hours=8)))
            return dt_utc8.strftime("%Y-%m-%d %H:%M:%S+08:00")
        except:
            # Fallback: assume it's already in correct format or add time
            if " " not in date_str:
                return f"{date_str} 00:00:00+08:00"
            return date_str

# FlexHR API Functions (to be registered with the agent)

async def login_submitter(
    user_type: str = "submitter"
) -> Dict[str, Any]:
    """
    Login to FlexHR as submitter or approver to obtain session token.
    
    Args:
        user_type: Either "submitter" or "approver"
        
    Returns:
        Dict containing login result and token
    """
    api = FlexHRLeaveAPI()
    
    if user_type not in ["submitter", "approver"]:
        return {
            "status": "error",
            "error": "user_type must be either 'submitter' or 'approver'"
        }
    
    credentials = TEST_CREDENTIALS[user_type]
    
    payload = {
        **credentials,
        **DEV_CONSTANTS
    }
    
    result = await api._make_request("/MDP/LoginDevice", payload)
    
    if result["status"] == "success":
        # Extract token from response
        token_data = result["data"]
        if "token" in token_data:
            api.session_token = token_data["token"]
            api.current_devid = DEV_CONSTANTS["devid"]
            api.current_user_type = user_type
            
            return {
                "status": "success",
                "message": f"Successfully logged in as {user_type}",
                "token": token_data["token"],
                "devid": DEV_CONSTANTS["devid"],
                "user_type": user_type
            }
        else:
            return {
                "status": "error",
                "error": "Login response did not contain token"
            }
    
    return result

async def leave_entitlement_summary(
    token: str,
    devid: str,
    empnum: str = "lee001",
    entlyr: str = None,
    isrfsh: str = "true"
) -> Dict[str, Any]:
    """
    Get leave entitlement summary for an employee.
    
    Args:
        token: Session token from login
        devid: Device ID (must match login)
        empnum: Employee number (default: lee001)
        entlyr: Entitlement year (default: current year)
        isrfsh: Refresh flag (default: "true")
        
    Returns:
        Dict containing entitlement summary
    """
    api = FlexHRLeaveAPI()
    
    if not entlyr:
        entlyr = str(datetime.now().year)
    
    payload = {
        "token": token,
        "devid": devid,
        "isrfsh": isrfsh,
        "empnum": empnum,
        "entlyr": entlyr,
        "startDate": ""
    }
    
    result = await api._make_request("/mLeavz/LeaveEntitlementSummary", payload)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "message": f"Retrieved entitlement summary for {empnum} ({entlyr})",
            "data": result["data"],
            "employee": empnum,
            "year": entlyr
        }
    
    return result

async def leave_entitlement_detail(
    token: str,
    devid: str,
    empnum: str = "lee001",
    entlyr: str = None,
    lvecode: str = "#AL",
    isrfsh: str = "true"
) -> Dict[str, Any]:
    """
    Get detailed leave entitlement for a specific leave code.
    
    Args:
        token: Session token from login
        devid: Device ID (must match login)
        empnum: Employee number (default: lee001)
        entlyr: Entitlement year (default: current year)
        lvecode: Leave code (e.g., "#AL" for Annual Leave)
        isrfsh: Refresh flag (default: "true")
        
    Returns:
        Dict containing detailed entitlement information
    """
    api = FlexHRLeaveAPI()
    
    if not entlyr:
        entlyr = str(datetime.now().year)
    
    payload = {
        "token": token,
        "devid": devid,
        "isrfsh": isrfsh,
        "empnum": empnum,
        "entlyr": entlyr,
        "lvecode": lvecode,
        "startDate": "",
        "docref": ""
    }
    
    result = await api._make_request("/mLeavz/LeaveEntitlement", payload)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "message": f"Retrieved {lvecode} entitlement details for {empnum} ({entlyr})",
            "data": result["data"],
            "employee": empnum,
            "year": entlyr,
            "leave_code": lvecode
        }
    
    return result

async def leave_listing(
    token: str,
    devid: str,
    viewas: str = "P",
    dtfrm: str = None,
    dtto: str = None,
    statarr: str = "1,3,4,6,5,9",
    isrfsh: str = "true"
) -> Dict[str, Any]:
    """
    List leave documents/applications.
    
    Args:
        token: Session token from login
        devid: Device ID (must match login)
        viewas: View as ("P" for personal)
        dtfrm: Date from (YYYY-MM-DD, default: start of current year)
        dtto: Date to (YYYY-MM-DD, default: end of current year)
        statarr: Status array filter
        isrfsh: Refresh flag (default: "true")
        
    Returns:
        Dict containing list of leave applications
    """
    api = FlexHRLeaveAPI()
    
    current_year = datetime.now().year
    if not dtfrm:
        dtfrm = f"{current_year}-01-01"
    if not dtto:
        dtto = f"{current_year}-12-31"
    
    payload = {
        "token": token,
        "devid": devid,
        "isrfsh": isrfsh,
        "viewas": viewas,
        "statarr": statarr,
        "ttlstatarr": "1,3",
        "dtfrm": dtfrm,
        "dtto": dtto,
        "doctyparr": "",
        "ownnum": "",
        "perpgcnt": "1000",
        "nowcnt": "1",
        "dtmodify": datetime.now().strftime("%Y-%m-%d")
    }
    
    result = await api._make_request("/mLeavz/LeaveListing", payload)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "message": f"Retrieved leave listing from {dtfrm} to {dtto}",
            "data": result["data"],
            "date_range": f"{dtfrm} to {dtto}"
        }
    
    return result

async def leave_submit(
    token: str,
    devid: str,
    start_date: str,
    end_date: str = None,
    leave_code: str = "#AL",
    number_of_days: str = "1.0",
    submitter_remark: str = "",
    submitterempnum: str = "lee001",
    ownerempnum: str = "lee001"
) -> Dict[str, Any]:
    """
    Submit a leave request.
    
    Args:
        token: Session token from login
        devid: Device ID (must match login)
        start_date: Leave start date (YYYY-MM-DD)
        end_date: Leave end date (YYYY-MM-DD, defaults to start_date)
        leave_code: Leave code (default: "#AL")
        number_of_days: Number of days (default: "1.0")
        submitter_remark: Optional remarks
        submitterempnum: Submitter employee number (default: "lee001")
        ownerempnum: Owner employee number (default: "lee001")
        
    Returns:
        Dict containing submission result
    """
    api = FlexHRLeaveAPI()
    
    if not end_date:
        end_date = start_date
    
    # Format dates for FlexHR
    formatted_start = api._format_date_for_flexhr(start_date)
    formatted_end = api._format_date_for_flexhr(end_date)
    current_timestamp = api._get_current_timestamp()
    current_year = datetime.now().year
    
    # Build the leave entry array
    leave_entry = {
        "LeaveId": "00000000-0000-0000-0000-000000000000",
        "StartDate": formatted_start,
        "EndDate": formatted_end,
        "StartTime": "",
        "EndTime": "",
        "StartTimeVal": current_timestamp,
        "EndTimeVal": current_timestamp,
        "LeaveCode": leave_code,
        "NumberOfDays": str(number_of_days),
        "NumberOfHours": "0.0",
        "DaySession": "0",
        "EntitleYear": current_year,
        "IsAdvance": False,
        "ReasonCode": "",
        "AccidentRef": "",
        "MedicalRef": "",
        "SubmitterRemark": submitter_remark,
        "OwnerEmployeeNo": ownerempnum.upper(),
        "SubmitterType": "PE",
        "SlipName": "",
        "SlipData": "",
        "SubmitterEmployeeNo": submitterempnum.upper(),
        "LeaveCustomField": "",
        "Attr": "",
        "LeaveDuration": 0,
        "Platform": 2,
        "Attr1": "", "Attr2": "", "Attr3": "", "Attr4": "", "Attr5": "",
        "Attr6": "", "Attr7": "", "Attr8": "", "Attr9": "", "Attr10": "",
        "AttachmentList": [],
        "isLinkRemark": False,
        "SlipDescription": "",
        "FileExtension": "",
        "FileSize": "",
        "designatedAppr1": "", "designatedAppr2": "", "designatedAppr3": "",
        "designatedAppr4": "", "designatedAppr5": "",
        "verifier": "",
        "designatedAppr1EmpNo": "", "designatedAppr2EmpNo": "", "designatedAppr3EmpNo": "",
        "designatedAppr4EmpNo": "", "designatedAppr5EmpNo": "",
        "verifierEmpNo": "",
        "designatedNotf": [],
        "isDesignatedApproverEnabled": False,
        "DesignatedApprover": "",
        "isVerifierRequired": False,
        "isDesignatedNotificationEnabled": False,
        "DesignatedNotification": ""
    }
    
    # Convert to JSON string as required by API
    newlve_json = json.dumps([leave_entry])
    
    payload = {
        "token": token,
        "devid": devid,
        "isrfsh": "true",
        "submitterempnum": submitterempnum,
        "ownerempnum": ownerempnum,
        "docref": "",
        "newlve": newlve_json,
        "acttkn": "2"  # Submit action
    }
    
    result = await api._make_request("/mLeavz/LeaveSubmission", payload)
    
    if result["status"] == "success":
        return {
            "status": "success",
            "message": f"Successfully submitted {leave_code} leave request",
            "data": result["data"],
            "leave_details": {
                "start_date": start_date,
                "end_date": end_date,
                "leave_code": leave_code,
                "days": number_of_days,
                "remarks": submitter_remark
            }
        }
    
    return result

async def leave_action(
    token: str,
    devid: str,
    docrefarr: str,
    acttkn: str,
    rmk: str = ""
) -> Dict[str, Any]:
    """
    Take action on a leave request (withdraw, approve, reject).
    
    Args:
        token: Session token from login
        devid: Device ID (must match login)
        docrefarr: Document reference(s) to act upon
        acttkn: Action token ("5"=Withdraw, "6"=Approve, "8"=Reject)
        rmk: Optional remarks
        
    Returns:
        Dict containing action result
    """
    api = FlexHRLeaveAPI()
    
    action_names = {
        "5": "Withdraw",
        "6": "Approve", 
        "8": "Reject"
    }
    
    if acttkn not in action_names:
        return {
            "status": "error",
            "error": f"Invalid action token. Use 5=Withdraw, 6=Approve, 8=Reject"
        }
    
    payload = {
        "token": token,
        "devid": devid,
        "isrfsh": "true",
        "docrefarr": docrefarr,
        "acttkn": acttkn,
        "rmk": rmk
    }
    
    result = await api._make_request("/mLeavz/LeaveAction", payload)
    
    if result["status"] == "success":
        action_name = action_names[acttkn]
        return {
            "status": "success",
            "message": f"Successfully {action_name.lower()}ed leave request {docrefarr}",
            "data": result["data"],
            "action": action_name,
            "document_ref": docrefarr,
            "remarks": rmk
        }
    
    return result

# Convenience functions for specific actions

async def leave_withdraw(
    token: str,
    devid: str,
    docrefarr: str,
    rmk: str = ""
) -> Dict[str, Any]:
    """Withdraw a leave request."""
    return await leave_action(token, devid, docrefarr, "5", rmk)

async def leave_approve(
    token: str,
    devid: str,
    docrefarr: str,
    rmk: str = ""
) -> Dict[str, Any]:
    """Approve a leave request (approver only)."""
    return await leave_action(token, devid, docrefarr, "6", rmk)

async def leave_reject(
    token: str,
    devid: str,
    docrefarr: str,
    rmk: str = ""
) -> Dict[str, Any]:
    """Reject a leave request (approver only)."""
    return await leave_action(token, devid, docrefarr, "8", rmk)

# Set function metadata for the AI agent
login_submitter.__name__ = "login_submitter"
login_submitter.__doc__ = """
Login to FlexHR system as submitter or approver.
ALWAYS call this first before any other FlexHR operations.

Parameters:
- user_type: "submitter" for employee actions, "approver" for manager actions

Returns the session token and devid that must be used in all subsequent calls.
"""

leave_entitlement_summary.__name__ = "leave_entitlement_summary"
leave_entitlement_summary.__doc__ = """
Get leave entitlement summary showing available leave balances.

Parameters:
- token: Session token from login_submitter
- devid: Device ID from login_submitter (must match)
- empnum: Employee number (default: lee001)
- entlyr: Year for entitlements (default: current year)
"""

leave_entitlement_detail.__name__ = "leave_entitlement_detail"
leave_entitlement_detail.__doc__ = """
Get detailed entitlement information for a specific leave type.

Parameters:
- token: Session token from login_submitter
- devid: Device ID from login_submitter (must match)
- empnum: Employee number (default: lee001)
- entlyr: Year for entitlements (default: current year)
- lvecode: Leave code (e.g., "#AL" for Annual Leave, "#SL" for Sick Leave)
"""

leave_listing.__name__ = "leave_listing"
leave_listing.__doc__ = """
List leave applications to view status and get document references.

Parameters:
- token: Session token from login_submitter
- devid: Device ID from login_submitter (must match)
- viewas: View type (default: "P" for personal)
- dtfrm: Start date for listing (YYYY-MM-DD, default: current year start)
- dtto: End date for listing (YYYY-MM-DD, default: current year end)
"""

leave_submit.__name__ = "leave_submit"
leave_submit.__doc__ = """
Submit a new leave request.

Parameters:
- token: Session token from login_submitter
- devid: Device ID from login_submitter (must match)
- start_date: Leave start date (YYYY-MM-DD format)
- end_date: Leave end date (YYYY-MM-DD format, optional - defaults to start_date)
- leave_code: Leave type code (default: "#AL" for Annual Leave)
- number_of_days: Number of days to request (default: "1.0")
- submitter_remark: Optional comments/reason for leave
- submitterempnum: Employee submitting (default: lee001)
- ownerempnum: Employee taking leave (default: lee001)
"""

leave_withdraw.__name__ = "leave_withdraw"
leave_withdraw.__doc__ = """
Withdraw a previously submitted leave request.

Parameters:
- token: Session token from login_submitter
- devid: Device ID from login_submitter (must match)
- docrefarr: Document reference of leave to withdraw (get from leave_listing)
- rmk: Optional remarks for withdrawal
"""

leave_approve.__name__ = "leave_approve"
leave_approve.__doc__ = """
Approve a leave request (approver/manager only).
Must login as approver first.

Parameters:
- token: Session token from login_submitter (approver)
- devid: Device ID from login_submitter (must match)
- docrefarr: Document reference of leave to approve (get from leave_listing)
- rmk: Optional approval comments
"""

leave_reject.__name__ = "leave_reject"
leave_reject.__doc__ = """
Reject a leave request (approver/manager only).
Must login as approver first.

Parameters:
- token: Session token from login_submitter (approver)
- devid: Device ID from login_submitter (must match)
- docrefarr: Document reference of leave to reject (get from leave_listing)
- rmk: Optional rejection reason
"""
