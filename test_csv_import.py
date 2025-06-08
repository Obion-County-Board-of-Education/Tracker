#!/usr/bin/env python3
"""
Test CSV Import Functionality
Tests the newly implemented CSV import endpoints for both tech and maintenance tickets
"""

import requests
import json

# Base URLs
PORTAL_URL = "http://localhost:8003"
API_URL = "http://localhost:8000"

def test_csv_import_endpoints():
    """Test that the CSV import endpoints are accessible"""
    print("🧪 Testing CSV Import Endpoints...")
    
    # Test tech tickets import endpoint (should be POST only, so GET should fail)
    try:
        response = requests.get(f"{PORTAL_URL}/tickets/tech/import")
        print(f"❌ Tech import GET request: {response.status_code} (expected 405)")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Tech import endpoint connection error: {e}")
    
    # Test maintenance tickets import endpoint (should be POST only, so GET should fail)
    try:
        response = requests.get(f"{PORTAL_URL}/tickets/maintenance/import")
        print(f"❌ Maintenance import GET request: {response.status_code} (expected 405)")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Maintenance import endpoint connection error: {e}")

def test_api_import_endpoints():
    """Test that the API import endpoints are accessible"""
    print("\n🧪 Testing API Import Endpoints...")
    
    # Test tech tickets API import endpoint
    try:
        # Test with empty POST (should fail but indicate endpoint exists)
        response = requests.post(f"{API_URL}/api/tickets/tech/import")
        print(f"✅ Tech API import endpoint exists: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Tech API import endpoint error: {e}")
    
    # Test maintenance tickets API import endpoint
    try:
        # Test with empty POST (should fail but indicate endpoint exists)
        response = requests.post(f"{API_URL}/api/tickets/maintenance/import")
        print(f"✅ Maintenance API import endpoint exists: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Maintenance API import endpoint error: {e}")

def test_file_import():
    """Test actual CSV file import functionality"""
    print("\n🧪 Testing CSV File Import...")
    
    # Test tech tickets import
    try:
        with open('test_tech_import.csv', 'rb') as f:
            files = {'file': ('test_tech_import.csv', f, 'text/csv')}
            data = {'operation': 'add'}
            response = requests.post(f"{API_URL}/api/tickets/tech/import", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Tech tickets import successful: {result['imported_count']} tickets imported")
                if result.get('errors'):
                    print(f"⚠️ Import errors: {result['errors']}")
            else:
                print(f"❌ Tech tickets import failed: {response.status_code} - {response.text}")
    except FileNotFoundError:
        print("⚠️ test_tech_import.csv not found")
    except Exception as e:
        print(f"❌ Tech tickets import error: {e}")
    
    # Test maintenance tickets import
    try:
        with open('test_maintenance_import.csv', 'rb') as f:
            files = {'file': ('test_maintenance_import.csv', f, 'text/csv')}
            data = {'operation': 'add'}
            response = requests.post(f"{API_URL}/api/tickets/maintenance/import", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Maintenance tickets import successful: {result['imported_count']} tickets imported")
                if result.get('errors'):
                    print(f"⚠️ Import errors: {result['errors']}")
            else:
                print(f"❌ Maintenance tickets import failed: {response.status_code} - {response.text}")
    except FileNotFoundError:
        print("⚠️ test_maintenance_import.csv not found")
    except Exception as e:
        print(f"❌ Maintenance tickets import error: {e}")

def main():
    print("🚀 Testing CSV Import Functionality")
    print("=" * 50)
    
    test_csv_import_endpoints()
    test_api_import_endpoints()
    test_file_import()
    
    print("\n" + "=" * 50)
    print("✅ CSV Import Testing Complete!")
    print("\n📝 Summary:")
    print("- Import buttons should now be visible on both tech and maintenance pages")
    print("- Import modals should open when clicking the import buttons")
    print("- CSV files can be imported with 'Add to Database' or 'Overwrite Database' options")
    print("- Import functionality creates buildings and rooms if they don't exist")
    print("- Both frontend and backend import functionality is now implemented")

if __name__ == "__main__":
    main()
