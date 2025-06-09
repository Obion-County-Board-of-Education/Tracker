#!/usr/bin/env python3

import requests
import json
import sys

def test_complete_solution():
    """Test the complete CSV export-import cycle fix"""
    
    print("=" * 60)
    print("TESTING COMPLETE CSV EXPORT-IMPORT CYCLE FIX")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Tech Tickets Export (Import-Ready)
    print("\n1. Testing Tech Tickets Export (Import-Ready Format)")
    print("-" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export?import_ready=true")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Save export for testing
            with open("test_tech_export.csv", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # Check if problematic fields are excluded
            lines = response.text.split('\n')
            if lines:
                headers = lines[0].lower()
                excluded_fields = ['id', 'created_at', 'updated_at']
                missing_fields = [field for field in excluded_fields if field in headers]
                
                if missing_fields:
                    print(f"❌ ERROR: Export still contains problematic fields: {missing_fields}")
                else:
                    print("✅ SUCCESS: Export excludes problematic fields (id, created_at, updated_at)")
                    print(f"Headers: {lines[0]}")
        else:
            print(f"❌ ERROR: Export failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: Export test failed: {e}")
    
    # Test 2: Tech Tickets Import
    print("\n2. Testing Tech Tickets Import")
    print("-" * 50)
    
    try:
        # Create a test CSV for import
        test_csv_content = """title,description,issue_type,school,room,tag,status,created_by
Test Import Ticket,This is a test import,Software,Test School,Room 101,TEST001,new,TestUser
Another Import Test,Second test ticket,Hardware,Test School,Room 102,TEST002,open,TestUser2"""
        
        with open("test_import.csv", "w") as f:
            f.write(test_csv_content)
        
        # Import the test CSV
        with open("test_import.csv", "rb") as f:
            files = {"file": ("test_import.csv", f, "text/csv")}
            data = {"operation": "append"}
            response = requests.post(f"{base_url}/api/tickets/tech/import", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("imported_count", 0) > 0:
                print(f"✅ SUCCESS: Imported {result.get('imported_count')} tickets")
                if result.get("errors"):
                    print(f"Warnings: {result.get('errors')}")
            else:
                print(f"❌ ERROR: Import failed: {result}")
        else:
            print(f"❌ ERROR: Import failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: Import test failed: {e}")
    
    # Test 3: Maintenance Tickets Export (Import-Ready)
    print("\n3. Testing Maintenance Tickets Export (Import-Ready Format)")
    print("-" * 50)
    
    try:
        response = requests.get(f"{base_url}/api/tickets/maintenance/export?import_ready=true")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            lines = response.text.split('\n')
            if lines:
                headers = lines[0].lower()
                excluded_fields = ['id', 'created_at', 'updated_at']
                missing_fields = [field for field in excluded_fields if field in headers]
                
                if missing_fields:
                    print(f"❌ ERROR: Export still contains problematic fields: {missing_fields}")
                else:
                    print("✅ SUCCESS: Maintenance export excludes problematic fields")
                    print(f"Headers: {lines[0]}")
        else:
            print(f"❌ ERROR: Maintenance export failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: Maintenance export test failed: {e}")
    
    # Test 4: Maintenance Tickets Import
    print("\n4. Testing Maintenance Tickets Import")
    print("-" * 50)
    
    try:
        # Create a test CSV for maintenance import
        test_csv_content = """title,description,issue_type,school,room,status,created_by
Test Maintenance,This is a test maintenance ticket,Plumbing,Test School,Room 201,new,MaintenanceUser"""
        
        with open("test_maintenance_import.csv", "w") as f:
            f.write(test_csv_content)
        
        # Import the test CSV
        with open("test_maintenance_import.csv", "rb") as f:
            files = {"file": ("test_maintenance_import.csv", f, "text/csv")}
            data = {"operation": "append"}
            response = requests.post(f"{base_url}/api/tickets/maintenance/import", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("imported_count", 0) > 0:
                print(f"✅ SUCCESS: Imported {result.get('imported_count')} maintenance tickets")
                if result.get("errors"):
                    print(f"Warnings: {result.get('errors')}")
            else:
                print(f"❌ ERROR: Maintenance import failed: {result}")
        else:
            print(f"❌ ERROR: Maintenance import failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: Maintenance import test failed: {e}")
    
    # Test 5: Complete Cycle Test
    print("\n5. Testing Complete Export-Import Cycle")
    print("-" * 50)
    
    try:
        # Export tech tickets
        export_response = requests.get(f"{base_url}/api/tickets/tech/export?import_ready=true")
        if export_response.status_code == 200:
            # Save and re-import
            with open("cycle_test.csv", "w", encoding="utf-8") as f:
                f.write(export_response.text)
            
            with open("cycle_test.csv", "rb") as f:
                files = {"file": ("cycle_test.csv", f, "text/csv")}
                data = {"operation": "append"}
                import_response = requests.post(f"{base_url}/api/tickets/tech/import", files=files, data=data)
            
            if import_response.status_code == 200:
                result = import_response.json()
                if result.get("success"):
                    print("✅ SUCCESS: Complete export-import cycle works correctly")
                    print(f"Cycle imported {result.get('imported_count')} tickets")
                    if result.get("errors"):
                        print(f"Skipped entries (expected for empty rows): {len(result.get('errors'))}")
                else:
                    print(f"❌ ERROR: Cycle import failed: {result}")
            else:
                print(f"❌ ERROR: Cycle import failed with status {import_response.status_code}")
        else:
            print(f"❌ ERROR: Cycle export failed with status {export_response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: Complete cycle test failed: {e}")
    
    print("\n" + "=" * 60)
    print("CSV EXPORT-IMPORT CYCLE FIX TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_solution()
