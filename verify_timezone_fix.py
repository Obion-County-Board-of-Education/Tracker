import sys
import os
import requests
import json
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def write_log(message):
    """Write message to log file"""
    with open("timezone_test_results.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()}: {message}\n")

def test_timezone_functionality():
    """Test the timezone functionality and write results to file"""
    
    # Clear previous results
    with open("timezone_test_results.txt", "w", encoding="utf-8") as f:
        f.write("=== Timezone Test Results ===\n")
    
    write_log("Starting timezone functionality test...")
    
    # Test 1: Import and test timezone functions
    try:
        from ocs_shared_models.timezone_utils import central_now, format_central_time, get_central_timezone
        
        utc_time = datetime.utcnow()
        central_time = central_now()
        
        write_log(f"UTC Time: {utc_time}")
        write_log(f"Central Time: {central_time}")
        write_log(f"Formatted Central: {format_central_time(central_time)}")
        
        # Calculate time difference
        time_diff = central_time - utc_time
        hours_diff = time_diff.total_seconds() / 3600
        write_log(f"Time difference: {hours_diff:.1f} hours")
        
        if -6.5 <= hours_diff <= -4.5:
            write_log("✓ Timezone offset is correct for Central Time")
        else:
            write_log("✗ Timezone offset seems incorrect")
            
    except Exception as e:
        write_log(f"✗ Error testing timezone functions: {e}")
    
    # Test 2: Test API endpoints
    try:
        write_log("Testing API endpoints...")
        
        # Test tickets API
        response = requests.get("http://localhost:8001/tech/status/closed", timeout=5)
        if response.status_code == 200:
            tickets = response.json()
            write_log(f"✓ Tickets API responding - Found {len(tickets)} closed tech tickets")
            if tickets:
                first_ticket = tickets[0]
                write_log(f"Sample ticket timestamps:")
                write_log(f"  Created: {first_ticket.get('created_at', 'N/A')}")
                write_log(f"  Updated: {first_ticket.get('updated_at', 'N/A')}")
        else:
            write_log(f"✗ Tickets API error: {response.status_code}")
            
    except Exception as e:
        write_log(f"✗ Error testing tickets API: {e}")
        
    try:
        # Test portal service status
        response = requests.get("http://localhost:8000/api/service-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            write_log(f"✓ Portal API responding - Service status timestamp: {data.get('timestamp', 'N/A')}")
        else:
            write_log(f"✗ Portal API error: {response.status_code}")
            
    except Exception as e:
        write_log(f"✗ Error testing portal API: {e}")
    
    # Test 3: Test Docker containers
    try:
        import subprocess
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            containers = result.stdout.strip().split('\n')
            write_log(f"✓ Docker containers running: {', '.join(containers)}")
        else:
            write_log(f"✗ Docker ps error: {result.stderr}")
    except Exception as e:
        write_log(f"✗ Error checking Docker containers: {e}")
    
    write_log("=== Test Complete ===")

if __name__ == "__main__":
    test_timezone_functionality()
    print("Test results written to timezone_test_results.txt")
