import requests
import json
from datetime import datetime

def test_api_timezone():
    """Test if the API is returning Central Time timestamps"""
    try:
        # Test the tickets API
        print("Testing Tickets API...")
        response = requests.get("http://localhost:8001/tech/status/closed")
        if response.status_code == 200:
            tickets = response.json()
            print(f"Found {len(tickets)} closed tech tickets")
            if tickets:
                first_ticket = tickets[0]
                print(f"Sample ticket timestamps:")
                print(f"  Created: {first_ticket.get('created_at', 'N/A')}")
                print(f"  Updated: {first_ticket.get('updated_at', 'N/A')}")
        else:
            print(f"Tickets API error: {response.status_code}")
            
        # Test the portal service status
        print("\nTesting Portal Service Status...")
        response = requests.get("http://localhost:8000/api/service-status")
        if response.status_code == 200:
            data = response.json()
            print(f"Service status timestamp: {data.get('timestamp', 'N/A')}")
        else:
            print(f"Portal API error: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing APIs: {e}")

def test_current_time():
    """Show current times for comparison"""
    print("\n=== Current Time Comparison ===")
    print(f"System UTC: {datetime.utcnow()}")
    
    # Import and test our timezone functions
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from ocs_shared_models.timezone_utils import central_now, format_central_time
        
        central_time = central_now()
        print(f"Central Time: {central_time}")
        print(f"Formatted: {format_central_time(central_time)}")
        
        # Calculate difference
        utc_time = datetime.utcnow()
        time_diff = central_time - utc_time
        hours_diff = time_diff.total_seconds() / 3600
        print(f"Time difference: {hours_diff:.1f} hours")
        
        if -6.5 <= hours_diff <= -4.5:
            print("✓ Timezone offset looks correct for Central Time")
        else:
            print("✗ Timezone offset seems incorrect")
            
    except Exception as e:
        print(f"Error testing timezone functions: {e}")

if __name__ == "__main__":
    test_current_time()
    test_api_timezone()
