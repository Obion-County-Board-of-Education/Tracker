#!/usr/bin/env python3
import requests

def test_csv_headers():
    """Test if the exclude_ids parameter properly excludes ID fields from CSV headers"""
    base_url = "http://localhost:5002"
    
    print("Testing CSV Header Logic...")
    print("=" * 50)
    
    # Test 1: Regular export (should include all fields)
    print("\n1. Testing regular export (exclude_ids=false):")
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export?exclude_ids=false")
        if response.status_code == 200:
            # Get first line (headers)
            headers = response.text.split('\n')[0].strip()
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Headers: {headers}")
            
            # Check if ID fields are present
            has_id = 'id' in headers.lower()
            has_created_at = 'created_at' in headers.lower()
            has_updated_at = 'updated_at' in headers.lower()
            
            print(f"🔍 Contains 'id': {has_id}")
            print(f"🔍 Contains 'created_at': {has_created_at}")
            print(f"🔍 Contains 'updated_at': {has_updated_at}")
        else:
            print(f"❌ Failed with status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Import-ready export (should exclude ID fields)
    print("\n2. Testing import-ready export (exclude_ids=true):")
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export?exclude_ids=true")
        if response.status_code == 200:
            # Get first line (headers)
            headers = response.text.split('\n')[0].strip()
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Headers: {headers}")
            
            # Check if ID fields are absent
            has_id = 'id' in headers.lower()
            has_created_at = 'created_at' in headers.lower()
            has_updated_at = 'updated_at' in headers.lower()
            
            print(f"🔍 Contains 'id': {has_id}")
            print(f"🔍 Contains 'created_at': {has_created_at}")
            print(f"🔍 Contains 'updated_at': {has_updated_at}")
            
            # Validation
            if not has_id and not has_created_at and not has_updated_at:
                print("🎉 SUCCESS: Import-ready format working correctly!")
            else:
                print("❌ FAILED: Still contains ID/timestamp fields")
        else:
            print(f"❌ Failed with status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Filename check
    print("\n3. Testing filename generation:")
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export?exclude_ids=true")
        if response.status_code == 200:
            content_disposition = response.headers.get('content-disposition', '')
            print(f"📁 Content-Disposition: {content_disposition}")
            
            if 'import_ready' in content_disposition:
                print("🎉 SUCCESS: Filename indicates import-ready format!")
            else:
                print("❌ FAILED: Filename doesn't indicate import-ready format")
        else:
            print(f"❌ Failed with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_csv_headers()
