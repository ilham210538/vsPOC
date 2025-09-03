"""
Current datetime tool for Azure AI agents to get real-time date information
"""
import json
from datetime import datetime, timezone
from typing import Dict, Any

def get_current_datetime(timezone_name: str = "UTC") -> Dict[str, Any]:
    """
    Get the current date and time information.
    
    Args:
        timezone_name: Timezone to return the datetime in (default: UTC)
        
    Returns:
        Dict containing current datetime information
    """
    try:
        # Get current time in Singapore timezone (UTC+8) 
        from datetime import timezone, timedelta
        singapore_tz = timezone(timedelta(hours=8))
        now_singapore = datetime.now(singapore_tz)
        now_utc = datetime.now(timezone.utc)
        
        # Print for visibility
        print(f"📅 API Call: get_current_datetime()")
        print(f"📅 Current Date/Time: {now_singapore.strftime('%B %d, %Y at %H:%M:%S SGT')} | UTC: {now_utc.strftime('%B %d, %Y at %H:%M:%S UTC')}")
        
        # Return comprehensive datetime information using Singapore time as primary
        return {
            "status": "success",
            "current_datetime_utc": now_utc.isoformat(),
            "current_datetime_singapore": now_singapore.isoformat(),
            "current_date": now_singapore.strftime("%Y-%m-%d"),
            "current_time": now_singapore.strftime("%H:%M:%S"),
            "day_of_week": now_singapore.strftime("%A"),
            "month_name": now_singapore.strftime("%B"),
            "year": now_singapore.year,
            "formatted_date": now_singapore.strftime("%B %d, %Y"),
            "timezone": "Singapore Standard Time",
            "iso_date": now_singapore.strftime("%Y-%m-%d"),
            "iso_datetime": now_singapore.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting current datetime: {e}")
        return {
            "status": "error",
            "message": f"Failed to get current datetime: {str(e)}"
        }

if __name__ == "__main__":
    # Test the function
    result = get_current_datetime()
    print(json.dumps(result, indent=2))
