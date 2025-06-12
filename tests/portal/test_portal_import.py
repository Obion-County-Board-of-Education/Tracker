#!/usr/bin/env python3
"""
Test CSV Import via Portal
This script tests the portal-level CSV import functionality to identify issues
"""

import requests
import csv
import io
import time
from datetime import datetime

def create_test_csv():
    """Create a test CSV file for import"""
    csv_data = """id,title,description,issue_type,school,room,tag,status,created_by,created_at,updated_at
1,Portal Test Issue,Testing portal CSV import,Computer Hardware,Test School,Room 101,TAG001,open,Portal Test,2024-01-01 12:00:00,2024-01-01 12:00:00
2,Another Portal Test,Second test for portal import,Network,Test School,Room 102,TAG002,open,Portal Test,2024-01-01 12:00:00,2024-01-01 12:00:00"""
    return csv_data

def test_portal_import():
    """Test portal import functionality"""
    print("🧪 Testing Portal CSV Import Functionality")
    print("=" * 50)
    
    # Test tech tickets import
    print("\n📤 Testing Tech Tickets Portal Import...")
    
    try:
        csv_content = create_test_csv()
        files = {'file': ('test_tickets.csv', csv_content, 'text/csv')}
        data = {'operation': 'add'}
        
        response = requests.post(
            'http://localhost:8003/tickets/tech/import',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 303:
            print("✅ Portal import returned redirect (expected)")
            print(f"Redirect Location: {response.headers.get('location', 'No location header')}")
        elif response.status_code == 200:
            print("✅ Portal import successful")
        else:
            print(f"❌ Portal import failed with status {response.status_code}")
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing portal import: {e}")
    
    # Test maintenance tickets import
    print("\n📤 Testing Maintenance Tickets Portal Import...")
    
    try:
        # Create maintenance-specific CSV (no tag column)
        maintenance_csv = """id,title,description,issue_type,school,room,status,created_by,created_at,updated_at
1,Maintenance Portal Test,Testing maintenance portal CSV import,Electrical,Test School,Room 101,open,Portal Test,2024-01-01 12:00:00,2024-01-01 12:00:00"""
        
        files = {'file': ('test_maintenance.csv', maintenance_csv, 'text/csv')}
        data = {'operation': 'add'}
        
        response = requests.post(
            'http://localhost:8003/tickets/maintenance/import',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 303:
            print("✅ Maintenance portal import returned redirect (expected)")
            print(f"Redirect Location: {response.headers.get('location', 'No location header')}")
        elif response.status_code == 200:
            print("✅ Maintenance portal import successful")
        else:
            print(f"❌ Maintenance portal import failed with status {response.status_code}")
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing maintenance portal import: {e}")

def test_api_direct():
    """Test API import directly to compare"""
    print("\n🔗 Testing Direct API Import for Comparison...")
    
    try:
        csv_content = create_test_csv()
        files = {'file': ('test_tickets.csv', csv_content, 'text/csv')}
        data = {'operation': 'add'}
        
        response = requests.post(
            'http://localhost:8000/api/tickets/tech/import',
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"API Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API import successful: {result}")
        else:
            print(f"❌ API import failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API import: {e}")

def main():
    print(f"🕒 Starting Portal Import Test at {datetime.now()}")
    test_portal_import()
    test_api_direct()
    print(f"\n🕒 Test completed at {datetime.now()}")

if __name__ == "__main__":
    main()
