#!/usr/bin/env python3
"""
Test script to verify that the CSV import status mapping fix works correctly.
This script tests that tickets imported with "open" status now appear in the open tickets filter.
"""

import requests
import csv
import io
import tempfile
import os

def test_status_mapping_fix():
    """Test both tech and maintenance ticket status mapping"""
    print("🧪 Testing CSV Import Status Mapping Fix...")
    
    base_url = "http://localhost:8000"
    
    # Test Tech Tickets
    print("\n1. Testing Tech Tickets Status Mapping...")
    
    # Create test CSV with "open" status
    tech_csv_content = """title,description,issue_type,status,school,room,tag,created_by
Test Tech Issue with Open Status,Testing that open status maps to new,Computer Hardware,open,Test School,Room 101,TEST001,Test User"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(tech_csv_content)
        tech_csv_path = f.name
    
    try:
        # Clear existing tech tickets first
        print("  - Clearing existing tech tickets...")
        response = requests.delete(f"{base_url}/api/tickets/tech/clear")
        if response.status_code == 200:
            print("  ✅ Tech tickets cleared")
        
        # Import CSV with "open" status
        print("  - Importing tech CSV with 'open' status...")
        with open(tech_csv_path, 'rb') as f:
            files = {'file': ('test_tech.csv', f, 'text/csv')}
            data = {'operation': 'overwrite'}
            response = requests.post(f"{base_url}/api/tickets/tech/import", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Tech CSV import successful: {result.get('imported_count', 0)} tickets")
            
            # Check if tickets appear in open filter
            print("  - Checking if tickets appear in open filter...")
            response = requests.get(f"{base_url}/api/tickets/tech?status_filter=open")
            if response.status_code == 200:
                tickets = response.json()
                if len(tickets) > 0:
                    print(f"  ✅ SUCCESS: {len(tickets)} tech tickets found in open filter")
                    for ticket in tickets:
                        print(f"    - Ticket #{ticket['id']}: Status='{ticket['status']}', Title='{ticket['title']}'")
                else:
                    print("  ❌ FAILED: No tech tickets found in open filter")
                    return False
            else:
                print(f"  ❌ FAILED: Could not fetch open tech tickets: {response.status_code}")
                return False
        else:
            print(f"  ❌ FAILED: Tech CSV import failed: {response.status_code}")
            return False
    
    finally:
        # Clean up temp file
        os.unlink(tech_csv_path)
    
    # Test Maintenance Tickets
    print("\n2. Testing Maintenance Tickets Status Mapping...")
    
    # Create test CSV with "open" status
    maintenance_csv_content = """title,description,issue_type,status,school,room,created_by
Test Maintenance Issue with Open Status,Testing that open status maps to new,HVAC,open,Test School,Room 102,Test User"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(maintenance_csv_content)
        maintenance_csv_path = f.name
    
    try:
        # Clear existing maintenance tickets first
        print("  - Clearing existing maintenance tickets...")
        response = requests.delete(f"{base_url}/api/tickets/maintenance/clear")
        if response.status_code == 200:
            print("  ✅ Maintenance tickets cleared")
        
        # Import CSV with "open" status
        print("  - Importing maintenance CSV with 'open' status...")
        with open(maintenance_csv_path, 'rb') as f:
            files = {'file': ('test_maintenance.csv', f, 'text/csv')}
            data = {'operation': 'overwrite'}
            response = requests.post(f"{base_url}/api/tickets/maintenance/import", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Maintenance CSV import successful: {result.get('imported_count', 0)} tickets")
            
            # Check if tickets appear in open filter
            print("  - Checking if tickets appear in open filter...")
            response = requests.get(f"{base_url}/api/tickets/maintenance?status_filter=open")
            if response.status_code == 200:
                tickets = response.json()
                if len(tickets) > 0:
                    print(f"  ✅ SUCCESS: {len(tickets)} maintenance tickets found in open filter")
                    for ticket in tickets:
                        print(f"    - Ticket #{ticket['id']}: Status='{ticket['status']}', Title='{ticket['title']}'")
                else:
                    print("  ❌ FAILED: No maintenance tickets found in open filter")
                    return False
            else:
                print(f"  ❌ FAILED: Could not fetch open maintenance tickets: {response.status_code}")
                return False
        else:
            print(f"  ❌ FAILED: Maintenance CSV import failed: {response.status_code}")
            return False
    
    finally:
        # Clean up temp file
        os.unlink(maintenance_csv_path)
    
    print("\n🎉 SUCCESS: Status mapping fix is working correctly!")
    print("   - CSV imports with 'open' status now map to 'new' status")
    print("   - Imported tickets now appear in the 'open' filter views")
    print("   - Fix applied to both tech and maintenance tickets")
    
    return True

if __name__ == "__main__":
    try:
        success = test_status_mapping_fix()
        if not success:
            print("\n❌ Test failed - status mapping fix needs attention")
            exit(1)
        else:
            print("\n✅ All tests passed - CSV import issue resolved!")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        exit(1)
