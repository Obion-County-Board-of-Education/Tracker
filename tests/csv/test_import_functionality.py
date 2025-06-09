#!/usr/bin/env python3
"""
Test script to verify CSV import functionality is working correctly.
"""

import requests
import csv
import io
import sys

def test_portal_accessible():
    """Test that the portal is accessible"""
    try:
        response = requests.get("http://localhost:8003/tickets/tech", timeout=10)
        if response.status_code == 200:
            print("✓ Portal is accessible")
            return True
        else:
            print(f"✗ Portal returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Portal is not accessible: {e}")
        return False

def test_import_endpoints():
    """Test that import endpoints exist"""
    endpoints = [
        "http://localhost:8000/api/tickets/tech/import",
        "http://localhost:8000/api/tickets/maintenance/import"
    ]
    
    for endpoint in endpoints:
        try:
            # Create a simple test CSV
            csv_content = "title,description,reporter,assigned_to,status,priority,building\nTest,Test Description,Test User,Test Assignee,open,medium,Main Office"
            files = {'file': ('test.csv', csv_content, 'text/csv')}
            data = {'import_mode': 'add'}
            
            response = requests.post(endpoint, files=files, data=data, timeout=10)
            
            if response.status_code in [200, 201]:
                print(f"✓ Import endpoint working: {endpoint}")
            else:
                print(f"✗ Import endpoint failed: {endpoint} - Status: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"✗ Error testing {endpoint}: {e}")

def test_portal_import_routes():
    """Test that portal import routes exist"""
    routes = [
        "http://localhost:8003/tickets/tech/import",
        "http://localhost:8003/tickets/maintenance/import"
    ]
    
    for route in routes:
        try:
            # Create a simple test CSV
            csv_content = "title,description,reporter,assigned_to,status,priority,building\nTest Portal,Test Description,Test User,Test Assignee,open,medium,Main Office"
            files = {'file': ('test.csv', csv_content, 'text/csv')}
            data = {'import_mode': 'add'}
            
            response = requests.post(route, files=files, data=data, timeout=10)
            
            if response.status_code in [200, 302]:  # 302 for redirect after successful import
                print(f"✓ Portal import route working: {route}")
            else:
                print(f"✗ Portal import route failed: {route} - Status: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"✗ Error testing {route}: {e}")

def main():
    print("Testing CSV Import Functionality")
    print("=" * 40)
    
    # Test basic connectivity
    if not test_portal_accessible():
        print("Portal is not accessible. Make sure services are running.")
        sys.exit(1)
    
    print("\nTesting API Import Endpoints:")
    test_import_endpoints()
    
    print("\nTesting Portal Import Routes:")
    test_portal_import_routes()
    
    print("\n" + "=" * 40)
    print("Import functionality testing complete!")
    print("\nTo test the UI:")
    print("1. Open http://localhost:8003/tickets/tech")
    print("2. Look for the 'Import CSV' button next to 'Export CSV'")
    print("3. Click 'Import CSV' and test file upload")
    print("4. Repeat for http://localhost:8003/tickets/maintenance")

if __name__ == "__main__":
    main()
