#!/usr/bin/env python3
"""
Final verification that CSV import functionality is working correctly.
Tests both UI accessibility and import functionality.
"""

import requests
import csv
import io
import sys

def test_portal_pages():
    """Test that portal pages are accessible"""
    pages = [
        "http://localhost:8003/tickets/tech/open",
        "http://localhost:8003/tickets/maintenance/open"
    ]
    
    all_working = True
    for page in pages:
        try:
            response = requests.get(page, timeout=10)
            if response.status_code == 200:
                print(f"✓ {page} - Accessible")
                
                # Check for import button in the HTML
                if 'Import CSV' in response.text:
                    print(f"  ✓ Import CSV button found")
                else:
                    print(f"  ✗ Import CSV button NOT found")
                    all_working = False
                    
                # Check for export button
                if 'Export CSV' in response.text:
                    print(f"  ✓ Export CSV button found")
                else:
                    print(f"  ✗ Export CSV button NOT found")
                    
            else:
                print(f"✗ {page} - Status: {response.status_code}")
                all_working = False
        except Exception as e:
            print(f"✗ {page} - Error: {e}")
            all_working = False
    
    return all_working

def test_import_functionality():
    """Test CSV import endpoints"""
    print("\nTesting CSV Import Functionality:")
    
    # Test tech tickets import
    tech_csv = """title,description,reporter,assigned_to,status,priority,building
Test Import Tech,Test CSV import functionality,Test User,Tech Staff,open,medium,Main Office"""
    
    try:
        files = {'file': ('test_tech.csv', tech_csv, 'text/csv')}
        data = {'operation': 'add'}  # Changed from import_mode to operation
        
        response = requests.post(
            "http://localhost:8003/tickets/tech/import",
            files=files,
            data=data,
            timeout=10,
            allow_redirects=False  # Don't follow redirects to see the response
        )
        
        if response.status_code in [200, 302, 303]:
            print(f"✓ Tech tickets import endpoint working - Status: {response.status_code}")
        else:
            print(f"✗ Tech tickets import failed - Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"✗ Error testing tech import: {e}")
    
    # Test maintenance tickets import
    maintenance_csv = """title,description,reporter,assigned_to,status,priority,building
Test Import Maintenance,Test CSV import functionality,Test User,Maintenance Staff,open,medium,Main Office"""
    
    try:
        files = {'file': ('test_maintenance.csv', maintenance_csv, 'text/csv')}
        data = {'operation': 'add'}  # Changed from import_mode to operation
        
        response = requests.post(
            "http://localhost:8003/tickets/maintenance/import",
            files=files,
            data=data,
            timeout=10,
            allow_redirects=False
        )
        
        if response.status_code in [200, 302, 303]:
            print(f"✓ Maintenance tickets import endpoint working - Status: {response.status_code}")
        else:
            print(f"✗ Maintenance tickets import failed - Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"✗ Error testing maintenance import: {e}")

def test_api_health():
    """Test that APIs are responding"""
    print("\nTesting API Health:")
    
    apis = [
        "http://localhost:8000/health",  # Tickets API
        "http://localhost:8003"         # Portal
    ]
    
    for api in apis:
        try:
            response = requests.get(api, timeout=5)
            if response.status_code == 200:
                print(f"✓ {api} - Healthy")
            else:
                print(f"✗ {api} - Status: {response.status_code}")
        except Exception as e:
            print(f"✗ {api} - Error: {e}")

def main():
    print("🔍 Final CSV Import Verification")
    print("=" * 50)
    
    # Test API health first
    test_api_health()
    
    # Test portal pages
    print("\nTesting Portal Pages:")
    pages_working = test_portal_pages()
    
    # Test import functionality
    test_import_functionality()
    
    print("\n" + "=" * 50)
    if pages_working:
        print("🎉 SUCCESS: Portal pages are accessible and import buttons are visible!")
    else:
        print("❌ ISSUES: Some portal functionality is not working correctly")
        
    print("\n📝 Manual Verification Steps:")
    print("1. Open http://localhost:8003/tickets/tech/open")
    print("2. Verify 'Import CSV' button is visible next to 'Export CSV'")
    print("3. Click 'Import CSV' and test file upload")
    print("4. Repeat for http://localhost:8003/tickets/maintenance/open")
    print("5. Test both 'Add to Database' and 'Overwrite Database' options")

if __name__ == "__main__":
    main()
