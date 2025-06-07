"""
Timezone utilities for OCS Portal
Handles conversion between UTC and Central Time (US/Central)
"""
from datetime import datetime, timezone, timedelta
import calendar

def get_central_timezone():
    """Get Central timezone object (-6 hours for CST, -5 hours for CDT)"""
    # This is a simplified approach - in production you might want to use pytz
    # Central Standard Time is UTC-6, Central Daylight Time is UTC-5
    
    # Simple daylight saving time detection
    now = datetime.now()
    
    # Daylight saving time typically runs from second Sunday in March to first Sunday in November
    # This is a simplified check
    is_dst = (now.month > 3 and now.month < 11) or \
             (now.month == 3 and now.day > 14) or \
             (now.month == 11 and now.day < 7)
    
    if is_dst:
        # Central Daylight Time (CDT) = UTC-5
        return timezone(timedelta(hours=-5))
    else:
        # Central Standard Time (CST) = UTC-6
        return timezone(timedelta(hours=-6))

def get_central_time():
    """Get current Central time"""
    central_tz = get_central_timezone()
    return datetime.now(central_tz)

def utc_to_central(utc_dt):
    """Convert UTC datetime to Central time"""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    central_tz = get_central_timezone()
    return utc_dt.astimezone(central_tz)

def central_now():
    """Get current time in Central timezone (naive datetime for database storage)"""
    central_tz = get_central_timezone()
    central_time = datetime.now(central_tz)
    # Return naive datetime (without timezone info) for database storage
    return central_time.replace(tzinfo=None)

def format_central_time(dt):
    """Format datetime for display in Central time"""
    if dt is None:
        return "N/A"
    
    # If it's a naive datetime, assume it's already in Central time
    if dt.tzinfo is None:
        return dt.strftime("%Y-%m-%d %I:%M:%S %p CST/CDT")
    
    # If it has timezone info, convert to Central
    central_dt = utc_to_central(dt)
    return central_dt.strftime("%Y-%m-%d %I:%M:%S %p CST/CDT")
