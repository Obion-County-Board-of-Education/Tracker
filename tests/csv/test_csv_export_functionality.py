#!/usr/bin/env python3
"""
Test script to verify CSV export functionality is working correctly
"""

import requests
import sys
from datetime import datetime

def test_api_exports():
    """Test the API export endpoints"""
    print("🔍 Testing API Export Endpoints...")
    
    # Test tech tickets export
    try:
        response = requests.get("http://localhost:8000/api/tickets/tech/export")
        if response.status_code == 200:
            print("✅ Tech tickets API export: SUCCESS")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content length: {len(response.content)} bytes")
            
            # Check if it's valid CSV
            lines = response.text.split('\n')
            if lines[0].startswith('ID,Title,Description'):
                print("   ✅ CSV format is correct")
            else:
                print("   ❌ CSV format is incorrect")
        else:
            print(f"❌ Tech tickets API export: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Tech tickets API export: ERROR - {e}")
    
    # Test maintenance tickets export
    try:
        response = requests.get("http://localhost:8000/api/tickets/maintenance/export")
        if response.status_code == 200:
            print("✅ Maintenance tickets API export: SUCCESS")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content length: {len(response.content)} bytes")
            
            # Check if it's valid CSV
            lines = response.text.split('\n')
            if lines[0].startswith('ID,Title,Description'):
                print("   ✅ CSV format is correct")
            else:
                print("   ❌ CSV format is incorrect")
        else:
            print(f"❌ Maintenance tickets API export: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Maintenance tickets API export: ERROR - {e}")

def test_portal_exports():
    """Test the portal export endpoints"""
    print("\n🔍 Testing Portal Export Endpoints...")
    
    # Test tech tickets export through portal
    try:
        response = requests.get("http://localhost:8003/tickets/tech/export")
        if response.status_code == 200:
            print("✅ Tech tickets portal export: SUCCESS")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content-Disposition: {response.headers.get('content-disposition')}")
            print(f"   Content length: {len(response.content)} bytes")
            
            # Check filename pattern
            content_disp = response.headers.get('content-disposition', '')
            if 'tech_tickets_export_' in content_disp and '.csv' in content_disp:
                print("   ✅ Filename format is correct")
            else:
                print("   ❌ Filename format is incorrect")
        else:
            print(f"❌ Tech tickets portal export: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Tech tickets portal export: ERROR - {e}")
    
    # Test maintenance tickets export through portal
    try:
        response = requests.get("http://localhost:8003/tickets/maintenance/export")
        if response.status_code == 200:
            print("✅ Maintenance tickets portal export: SUCCESS")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Content-Disposition: {response.headers.get('content-disposition')}")
            print(f"   Content length: {len(response.content)} bytes")
            
            # Check filename pattern
            content_disp = response.headers.get('content-disposition', '')
            if 'maintenance_tickets_export_' in content_disp and '.csv' in content_disp:
                print("   ✅ Filename format is correct")
            else:
                print("   ❌ Filename format is incorrect")
        else:
            print(f"❌ Maintenance tickets portal export: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Maintenance tickets portal export: ERROR - {e}")

def test_route_conflicts():
    """Test that export routes don't conflict with parameterized routes"""
    print("\n🔍 Testing Route Conflicts...")
    
    # Test that individual ticket routes still work
    try:
        # Get list of tech tickets first
        response = requests.get("http://localhost:8000/api/tickets/tech")
        if response.status_code == 200:
            tickets = response.json()
            if tickets:
                ticket_id = tickets[0]['id']
                
                # Test individual ticket route
                response = requests.get(f"http://localhost:8000/api/tickets/tech/{ticket_id}")
                if response.status_code == 200:
                    print("✅ Individual tech ticket route: SUCCESS")
                else:
                    print(f"❌ Individual tech ticket route: FAILED ({response.status_code})")
            else:
                print("⚠️  No tech tickets to test individual route")
        else:
            print(f"❌ Could not get tech tickets list ({response.status_code})")
    except Exception as e:
        print(f"❌ Route conflict test: ERROR - {e}")

def main():
    """Run all tests"""
    print("🚀 CSV Export Functionality Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    test_api_exports()
    test_portal_exports()
    test_route_conflicts()
    
    print("\n" + "=" * 50)
    print("✅ CSV Export Functionality Test Complete!")

if __name__ == "__main__":
    main()
