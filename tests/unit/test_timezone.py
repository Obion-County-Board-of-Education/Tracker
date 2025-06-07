#!/usr/bin/env python3
"""
Test script to verify timezone functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from ocs_shared_models.timezone_utils import central_now, format_central_time, get_central_timezone

def test_timezone():
    print("=== Timezone Test Results ===")
    
    # Get current times
    utc_time = datetime.utcnow()
    central_time = central_now()
    
    print(f"UTC Time: {utc_time}")
    print(f"Central Time (naive): {central_time}")
    print(f"Formatted Central: {format_central_time(central_time)}")
    
    # Check timezone offset
    central_tz = get_central_timezone()
    print(f"Central timezone offset: {central_tz}")
    
    # Calculate difference
    time_diff = central_time - utc_time
    hours_diff = time_diff.total_seconds() / 3600
    print(f"Time difference: {hours_diff} hours")
    
    print("\n=== Expected Results ===")
    print("- Central Time should be 5-6 hours behind UTC")
    print("- During DST (spring/summer): UTC-5 (CDT)")
    print("- During standard time (fall/winter): UTC-6 (CST)")

if __name__ == "__main__":
    test_timezone()
