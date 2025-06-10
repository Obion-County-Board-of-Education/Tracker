#!/usr/bin/env python3
"""
Test script to verify import-ready export functionality
"""
import requests
import csv
import io

def test_import_ready_exports():
    """Test that import-ready exports exclude problematic fields"""
    base_url = "http://localhost:8003"  # Container port
    
    # Test tech tickets import-ready export
    print("Testing Tech Tickets Import-Ready Export...")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export?import_ready=true")
        if response.status_code == 200:
            print("✅ Tech tickets import-ready export: SUCCESS")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            
            # Parse CSV to check headers
            csv_content = response.text
            reader = csv.reader(io.StringIO(csv_content))
            headers = next(reader)
            
            print(f"   Headers: {headers}")
            
            # Check for problematic fields
            problematic_fields = ['id', 'created_at', 'updated_at']
            has_problematic = any(field in headers for field in problematic_fields)
            
            if not has_problematic:
                print("   ✅ No problematic fields (id, created_at, updated_at) in export")
                
                # Count data rows
                data_rows = list(reader)
                print(f"   ✅ Contains {len(data_rows)} data rows")
                
                # Show expected headers for import-ready format
                expected_headers = ['title', 'description', 'issue_type', 'school', 'room', 'tag', 'status', 'created_by']
                if headers == expected_headers:
                    print("   ✅ Headers match expected import-ready format")
                else:
                    print(f"   ⚠️  Headers don't match expected format")
                    print(f"      Expected: {expected_headers}")
                    print(f"      Got:      {headers}")
            else:
                print("   ❌ Still contains problematic fields:")
                for field in problematic_fields:
                    if field in headers:
                        print(f"       - {field}")
                        
        else:
            print(f"❌ Tech tickets import-ready export failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing tech import-ready export: {e}")
    
    # Test maintenance tickets import-ready export
    print("\nTesting Maintenance Tickets Import-Ready Export...")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/tickets/maintenance/export?import_ready=true")
        if response.status_code == 200:
            print("✅ Maintenance tickets import-ready export: SUCCESS")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            
            # Parse CSV to check headers
            csv_content = response.text
            reader = csv.reader(io.StringIO(csv_content))
            headers = next(reader)
            
            print(f"   Headers: {headers}")
            
            # Check for problematic fields
            problematic_fields = ['id', 'created_at', 'updated_at']
            has_problematic = any(field in headers for field in problematic_fields)
            
            if not has_problematic:
                print("   ✅ No problematic fields (id, created_at, updated_at) in export")
                
                # Count data rows
                data_rows = list(reader)
                print(f"   ✅ Contains {len(data_rows)} data rows")
                
                # Show expected headers for import-ready format (no 'tag' for maintenance)
                expected_headers = ['title', 'description', 'issue_type', 'school', 'room', 'status', 'created_by']
                if headers == expected_headers:
                    print("   ✅ Headers match expected import-ready format")
                else:
                    print(f"   ⚠️  Headers don't match expected format")
                    print(f"      Expected: {expected_headers}")
                    print(f"      Got:      {headers}")
            else:
                print("   ❌ Still contains problematic fields:")
                for field in problematic_fields:
                    if field in headers:
                        print(f"       - {field}")
                        
        else:
            print(f"❌ Maintenance tickets import-ready export failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing maintenance import-ready export: {e}")
    
    # Test comparison with regular exports
    print("\nTesting Regular Exports (should include all fields)...")
    print("=" * 50)
    
    try:
        # Test regular tech export
        response = requests.get(f"{base_url}/api/tickets/tech/export")
        if response.status_code == 200:
            csv_content = response.text
            reader = csv.reader(io.StringIO(csv_content))
            headers = next(reader)
            
            print(f"Tech regular export headers: {headers}")
            if 'id' in headers and 'created_at' in headers and 'updated_at' in headers:
                print("   ✅ Regular tech export includes all fields")
            else:
                print("   ❌ Regular tech export missing expected fields")
        
        # Test regular maintenance export
        response = requests.get(f"{base_url}/api/tickets/maintenance/export")
        if response.status_code == 200:
            csv_content = response.text
            reader = csv.reader(io.StringIO(csv_content))
            headers = next(reader)
            
            print(f"Maintenance regular export headers: {headers}")
            if 'id' in headers and 'created_at' in headers and 'updated_at' in headers:
                print("   ✅ Regular maintenance export includes all fields")
            else:
                print("   ❌ Regular maintenance export missing expected fields")
                
    except Exception as e:
        print(f"❌ Error testing regular exports: {e}")

if __name__ == "__main__":
    test_import_ready_exports()
