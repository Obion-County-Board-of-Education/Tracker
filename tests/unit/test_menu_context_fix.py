#!/usr/bin/env python3
"""
Test script to verify menu context fixes for Users and Buildings pages
"""

import requests
import sys

def test_page(url, page_name):
    """Test a page and check for successful response"""
    try:
        print(f"\n🧪 Testing {page_name}...")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Status: {response.status_code} OK")
            
            # Check if the response contains HTML (not an error page)
            if 'html' in response.headers.get('content-type', '').lower():
                print(f"   ✅ Content-Type: HTML response")
                
                # Check for specific content that indicates success
                if 'menu_visibility' in response.text:
                    print(f"   ✅ Menu context: Present in template")
                elif 'base.html' in response.text or 'OCS Portal' in response.text:
                    print(f"   ✅ Template: Rendered successfully")
                else:
                    print(f"   ⚠️  Template: Basic HTML but may have issues")
                
                # Check for Jinja2 errors
                if 'jinja2.exceptions.UndefinedError' in response.text:
                    print(f"   ❌ Jinja2 Error: Still present")
                    return False
                elif 'menu_visibility\' is undefined' in response.text:
                    print(f"   ❌ Menu Error: menu_visibility still undefined")
                    return False
                else:
                    print(f"   ✅ No Jinja2 errors detected")
                
                return True
            else:
                print(f"   ❌ Content-Type: {response.headers.get('content-type', 'unknown')}")
                return False
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   ❌ Error: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected Error: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 OCS Portal - Menu Context Fix Verification")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test pages that should now have menu context
    test_cases = [
        (f"{base_url}/users", "Users Page (Redirect)"),
        (f"{base_url}/users/list", "Users List"),
        (f"{base_url}/buildings", "Buildings Page (Redirect)"),
        (f"{base_url}/buildings/list", "Buildings List"),
        (f"{base_url}/users/add", "Add User Form"),
        (f"{base_url}/buildings/add", "Add Building Form"),
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for url, page_name in test_cases:
        if test_page(url, page_name):
            successful_tests += 1
    
    print(f"\n" + "=" * 50)
    print(f"📊 Test Results: {successful_tests}/{total_tests} pages working")
    
    if successful_tests == total_tests:
        print("🎉 All pages are working correctly!")
        print("✅ Menu context fix was successful")
    elif successful_tests > 0:
        print("⚠️  Some pages are working, but issues remain")
    else:
        print("❌ All pages failed - menu context fix needs more work")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
