#!/usr/bin/env python3

import requests
import sys

def test_route_directly():
    """Test the export route directly to see what's happening"""
    
    base_url = "http://localhost:8000"
    
    print("Testing export route with import_ready parameter...")
    
    # Test 1: Without parameter (should include IDs)
    print("\n=== Test 1: Without import_ready parameter ===")
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            lines = response.text.split('\n')
            if lines:
                headers = lines[0].split(',')
                print(f"Headers: {headers}")
                if 'id' in headers:
                    print("✅ Contains 'id' field (expected for full export)")
                else:
                    print("❌ Missing 'id' field (unexpected)")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: With import_ready=true (should exclude IDs)
    print("\n=== Test 2: With import_ready=true ===")
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export?import_ready=true")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            lines = response.text.split('\n')
            if lines:
                headers = lines[0].split(',')
                print(f"Headers: {headers}")
                if 'id' in headers:
                    print("❌ Still contains 'id' field (parameter not working!)")
                else:
                    print("✅ No 'id' field (parameter working correctly)")
        
        # Save for inspection
        with open("test_with_parameter.csv", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Saved response to test_with_parameter.csv")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Different parameter values
    print("\n=== Test 3: Different parameter formats ===")
    test_values = ["1", "True", "yes", "on", "false", "0"]
    
    for value in test_values:
        try:
            response = requests.get(f"{base_url}/api/tickets/tech/export?import_ready={value}")
            if response.status_code == 200:
                lines = response.text.split('\n')
                if lines:
                    headers = lines[0].split(',')
                    has_id = 'id' in headers
                    print(f"import_ready={value} -> {'HAS id' if has_id else 'NO id'}")
        except Exception as e:
            print(f"Error with {value}: {e}")

if __name__ == "__main__":
    test_route_directly()
