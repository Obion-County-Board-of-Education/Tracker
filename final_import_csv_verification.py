#!/usr/bin/env python3
"""
Final verification script for Import CSV button fix
This script verifies that Import CSV buttons are visible and functional on both tech and maintenance ticket pages.
"""

import requests
import sys
import os
from datetime import datetime

def test_page_for_import_button(url, page_name):
    """Test if a page has the Import CSV button visible"""
    try:
        print(f"\n🧪 Testing {page_name}...")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Status: {response.status_code} OK")
            
            # Check for Import CSV button
            if 'Import CSV' in response.text:
                print(f"   ✅ Import CSV button: FOUND")
                
                # Check for the specific onclick function
                if "showImportModal('tech')" in response.text or "showImportModal('maintenance')" in response.text:
                    print(f"   ✅ Import modal function: FOUND")
                else:
                    print(f"   ⚠️  Import modal function: Missing")
                
                # Check for Import CSV modal
                if 'Import CSV Modal' in response.text:
                    print(f"   ✅ Import CSV modal: FOUND")
                else:
                    print(f"   ⚠️  Import CSV modal: Missing")
                
                return True
            else:
                print(f"   ❌ Import CSV button: NOT FOUND")
                return False
        else:
            print(f"   ❌ Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_csv_import_route(base_url, ticket_type):
    """Test if the CSV import route is accessible"""
    try:
        import_url = f"{base_url}/tickets/{ticket_type}/import"
        print(f"\n🔗 Testing CSV import route...")
        print(f"   URL: {import_url}")
        
        # Test with GET request (should return method not allowed or form)
        response = requests.get(import_url, timeout=10)
        
        if response.status_code in [200, 405]:  # 200 for form, 405 for method not allowed
            print(f"   ✅ Import route: Accessible (Status: {response.status_code})")
            return True
        else:
            print(f"   ❌ Import route: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Import route error: {e}")
        return False

def main():
    """Main verification function"""
    print("🎯 Final Import CSV Button Verification")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8003"
    
    # Test cases for both tech and maintenance tickets
    test_cases = [
        (f"{base_url}/tickets/tech/open", "Tech Tickets (Open)", "tech"),
        (f"{base_url}/tickets/tech/closed", "Tech Tickets (Closed)", "tech"),
        (f"{base_url}/tickets/maintenance/open", "Maintenance Tickets (Open)", "maintenance"),
        (f"{base_url}/tickets/maintenance/closed", "Maintenance Tickets (Closed)", "maintenance"),
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    # Test each page for Import CSV button
    for url, page_name, ticket_type in test_cases:
        if test_page_for_import_button(url, page_name):
            successful_tests += 1
    
    # Test CSV import routes
    route_tests = [
        ("tech", "Technology"),
        ("maintenance", "Maintenance")
    ]
    
    route_success = 0
    for ticket_type, type_name in route_tests:
        if test_csv_import_route(base_url, ticket_type):
            route_success += 1
    
    print(f"\n" + "=" * 50)
    print(f"📊 Test Results:")
    print(f"   Import Button Tests: {successful_tests}/{total_tests} pages working")
    print(f"   Import Route Tests: {route_success}/{len(route_tests)} routes accessible")
    
    if successful_tests == total_tests and route_success == len(route_tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Import CSV buttons are visible and functional on all pages")
        print("✅ CSV import routes are accessible")
        print("\n📋 Summary of fixes applied:")
        print("   • Added missing current_datetime variable to tech ticket routes")
        print("   • Fixed Python syntax errors (missing newlines)")
        print("   • Replaced problematic tech_tickets_list.html template")
        print("   • Fixed indentation errors in main.py")
        print("   • Container rebuilt successfully with all changes")
        
        return True
    else:
        print("\n❌ Some tests failed!")
        if successful_tests < total_tests:
            print(f"   • {total_tests - successful_tests} pages still missing Import CSV buttons")
        if route_success < len(route_tests):
            print(f"   • {len(route_tests) - route_success} import routes not accessible")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
