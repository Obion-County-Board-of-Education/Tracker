#!/usr/bin/env python3
"""Test the export-for-import routes to verify routing fix"""

import requests
import json
import csv
import io

def test_export_for_import_routes():
    """Test that export-for-import routes work correctly"""
    
    base_url = "http://localhost:8000"
    
    # Test tech tickets export-for-import
    print("Testing tech tickets export-for-import route...")
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export-for-import")
        print(f"Tech export-for-import - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Tech export-for-import route works!")
            
            # Check if it's a CSV
            content_type = response.headers.get('content-type', '')
            if 'csv' in content_type.lower():
                print("✅ Returns CSV format")
                
                # Parse CSV to check headers
                content = response.text
                reader = csv.reader(io.StringIO(content))
                headers = next(reader)
                print(f"Headers: {headers}")
                
                # Check that problematic fields are not included
                problematic_fields = ['id', 'created_at', 'updated_at']
                has_problematic = any(field in headers for field in problematic_fields)
                
                if not has_problematic:
                    print("✅ No problematic fields (id, created_at, updated_at) in export")
                else:
                    print("❌ Still contains problematic fields")
                    
            else:
                print(f"❌ Wrong content type: {content_type}")
        else:
            print(f"❌ Tech export-for-import failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API - is Docker running?")
        return False
    except Exception as e:
        print(f"❌ Error testing tech export: {e}")
        return False
    
    # Test maintenance tickets export-for-import
    print("\nTesting maintenance tickets export-for-import route...")
    try:
        response = requests.get(f"{base_url}/api/tickets/maintenance/export-for-import")
        print(f"Maintenance export-for-import - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Maintenance export-for-import route works!")
            
            # Check if it's a CSV
            content_type = response.headers.get('content-type', '')
            if 'csv' in content_type.lower():
                print("✅ Returns CSV format")
                
                # Parse CSV to check headers
                content = response.text
                reader = csv.reader(io.StringIO(content))
                headers = next(reader)
                print(f"Headers: {headers}")
                
                # Check that problematic fields are not included
                problematic_fields = ['id', 'created_at', 'updated_at']
                has_problematic = any(field in headers for field in problematic_fields)
                
                if not has_problematic:
                    print("✅ No problematic fields (id, created_at, updated_at) in export")
                else:
                    print("❌ Still contains problematic fields")
                    
            else:
                print(f"❌ Wrong content type: {content_type}")
        else:
            print(f"❌ Maintenance export-for-import failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing maintenance export: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing export-for-import routes...")
    test_export_for_import_routes()
