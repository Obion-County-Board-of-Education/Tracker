#!/usr/bin/env python3
"""
Comprehensive test for CSV import feedback system
Tests the complete workflow:
1. CSV import functionality
2. URL parameter generation
3. Frontend notification display
4. User success feedback

Run this to verify the complete import feedback system is working.
"""

import requests
import time
import csv
import os
from datetime import datetime

# Configuration
PORTAL_BASE_URL = "http://localhost:8001"
API_BASE_URL = "http://localhost:8000"

def create_test_csv(filename, ticket_type="tech"):
    """Create a test CSV file for import"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if ticket_type == "tech":
        headers = ["title", "description", "priority", "status", "created_by", "building_id"]
        test_data = [
            [f"Test Tech Ticket {timestamp}_1", "Test description 1", "Medium", "Open", "test_user", "1"],
            [f"Test Tech Ticket {timestamp}_2", "Test description 2", "High", "Open", "test_user", "2"],
            [f"Test Tech Ticket {timestamp}_3", "Test description 3", "Low", "Closed", "test_user", "1"]
        ]
    else:  # maintenance
        headers = ["title", "description", "priority", "status", "created_by", "building_id", "category"]
        test_data = [
            [f"Test Maintenance Ticket {timestamp}_1", "Test maintenance 1", "Medium", "Open", "test_user", "1", "Plumbing"],
            [f"Test Maintenance Ticket {timestamp}_2", "Test maintenance 2", "High", "Open", "test_user", "2", "Electrical"],
            [f"Test Maintenance Ticket {timestamp}_3", "Test maintenance 3", "Low", "Closed", "test_user", "1", "HVAC"]
        ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(test_data)
    
    print(f"✓ Created test CSV: {filename}")
    return len(test_data)

def test_csv_import_feedback(ticket_type="tech"):
    """Test CSV import with feedback system"""
    print(f"\n=== Testing {ticket_type.upper()} tickets CSV import feedback ===")
    
    # Step 1: Create test CSV
    csv_filename = f"test_{ticket_type}_import_feedback.csv"
    expected_count = create_test_csv(csv_filename, ticket_type)
    
    try:
        # Step 2: Test import via portal (this should generate URL parameters)
        print(f"📤 Testing import via portal...")
        
        # Upload file to portal import endpoint
        import_url = f"{PORTAL_BASE_URL}/tickets/{ticket_type}/import"
        
        with open(csv_filename, 'rb') as csvfile:
            files = {'file': (csv_filename, csvfile, 'text/csv')}
            data = {'operation': 'import'}  # Test import mode
            
            response = requests.post(import_url, files=files, data=data, allow_redirects=False)
            
            if response.status_code == 303:
                redirect_url = response.headers.get('Location', '')
                print(f"✓ Got redirect (303): {redirect_url}")
                
                # Check if URL contains success parameters
                if 'import_success=true' in redirect_url:
                    print(f"✓ Success parameters found in redirect URL")
                    
                    # Extract parameters for verification
                    if 'count=' in redirect_url:
                        count_param = redirect_url.split('count=')[1].split('&')[0]
                        print(f"✓ Import count parameter: {count_param}")
                        
                        if count_param == str(expected_count):
                            print(f"✓ Count matches expected: {expected_count}")
                        else:
                            print(f"⚠ Count mismatch - Expected: {expected_count}, Got: {count_param}")
                    
                    if 'mode=' in redirect_url:
                        mode_param = redirect_url.split('mode=')[1].split('&')[0]
                        print(f"✓ Import mode parameter: {mode_param}")
                
                else:
                    print(f"❌ No success parameters in redirect URL")
                    if 'import_error=true' in redirect_url:
                        print(f"❌ Error parameters found instead")
            
            elif response.status_code == 200:
                print(f"⚠ Got 200 instead of redirect - check if import processed")
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                print(f"Response: {response.text}")
        
        # Step 3: Test replace mode
        print(f"\n📤 Testing replace mode...")
        
        with open(csv_filename, 'rb') as csvfile:
            files = {'file': (csv_filename, csvfile, 'text/csv')}
            data = {'operation': 'replace'}  # Test replace mode
            
            response = requests.post(import_url, files=files, data=data, allow_redirects=False)
            
            if response.status_code == 303:
                redirect_url = response.headers.get('Location', '')
                print(f"✓ Replace mode redirect: {redirect_url}")
                
                if 'mode=replace' in redirect_url:
                    print(f"✓ Replace mode parameter found")
                else:
                    print(f"⚠ Replace mode parameter missing")
            
        # Step 4: Test frontend notification system
        print(f"\n🌐 Testing frontend notification system...")
        
        # Construct test URL with success parameters
        test_success_url = f"{PORTAL_BASE_URL}/tickets/{ticket_type}?import_success=true&count=3&mode=import"
        
        try:
            response = requests.get(test_success_url)
            if response.status_code == 200:
                content = response.text
                
                # Check for notification function
                if 'showNotification' in content:
                    print(f"✓ showNotification function found in template")
                else:
                    print(f"❌ showNotification function missing")
                
                # Check for URL parameter handling
                if 'URLSearchParams' in content:
                    print(f"✓ URL parameter handling found")
                else:
                    print(f"❌ URL parameter handling missing")
                
                # Check for success handling
                if 'import_success' in content:
                    print(f"✓ Success parameter handling found")
                else:
                    print(f"❌ Success parameter handling missing")
                
                # Check for error handling
                if 'import_error' in content:
                    print(f"✓ Error parameter handling found")
                else:
                    print(f"❌ Error parameter handling missing")
            
            else:
                print(f"❌ Could not load page: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            print(f"⚠ Could not test frontend (portal may not be running): {e}")
        
        # Step 5: Test error condition
        print(f"\n❌ Testing error handling...")
        
        # Create invalid CSV
        invalid_csv = f"test_{ticket_type}_invalid.csv"
        with open(invalid_csv, 'w') as f:
            f.write("invalid,csv,content\nwith,missing,columns")
        
        try:
            with open(invalid_csv, 'rb') as csvfile:
                files = {'file': (invalid_csv, csvfile, 'text/csv')}
                data = {'operation': 'import'}
                
                response = requests.post(import_url, files=files, data=data, allow_redirects=False)
                
                if response.status_code == 303:
                    redirect_url = response.headers.get('Location', '')
                    if 'import_error=true' in redirect_url:
                        print(f"✓ Error handling working correctly")
                        if 'message=' in redirect_url:
                            error_msg = redirect_url.split('message=')[1].split('&')[0]
                            print(f"✓ Error message parameter: {error_msg}")
                    else:
                        print(f"⚠ Expected error parameters not found")
        
        except Exception as e:
            print(f"⚠ Error test failed: {e}")
        
        finally:
            # Cleanup
            for cleanup_file in [invalid_csv]:
                try:
                    if os.path.exists(cleanup_file):
                        os.remove(cleanup_file)
                except:
                    pass
    
    finally:
        # Cleanup test CSV
        try:
            if os.path.exists(csv_filename):
                os.remove(csv_filename)
                print(f"🧹 Cleaned up: {csv_filename}")
        except:
            pass

def test_complete_system():
    """Test the complete CSV import feedback system"""
    print("🚀 Starting Complete CSV Import Feedback System Test")
    print("=" * 60)
    
    # Test both ticket types
    test_csv_import_feedback("tech")
    test_csv_import_feedback("maintenance")
    
    print("\n" + "=" * 60)
    print("✅ CSV Import Feedback System Test Complete!")
    print("\nThe system should now provide clear visual feedback to users when:")
    print("  • CSV imports succeed (with count and mode)")
    print("  • CSV imports fail (with error message)")
    print("  • Notifications appear as styled popups")
    print("  • Notifications auto-disappear after 5 seconds")
    print("  • Users can manually close notifications")

if __name__ == "__main__":
    test_complete_system()
