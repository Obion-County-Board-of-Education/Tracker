#!/usr/bin/env python3
"""
Test Users and Buildings Pages
This script tests the critical pages that were previously failing
"""

import requests
import sys

def test_page(url, page_name):
    """Test a page and return results"""
    try:
        print(f"🧪 Testing {page_name} page at {url}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            # Check for common error indicators
            content = response.text.lower()
            if 'error' in content or 'exception' in content or 'traceback' in content:
                print(f"❌ {page_name}: Page loaded but contains error content")
                return False
            elif 'menu_visibility' in content:
                print(f"❌ {page_name}: Still has menu_visibility template error")
                return False
            else:
                print(f"✅ {page_name}: Page loaded successfully")
                return True
        else:
            print(f"❌ {page_name}: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {page_name}: Connection failed - service may be down")
        return False
    except Exception as e:
        print(f"❌ {page_name}: Error - {e}")
        return False

def main():
    """Test critical pages"""
    print("=" * 60)
    print("🔍 TESTING USERS AND BUILDINGS PAGES")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    test_results = []
    
    # Test Users pages
    test_results.append(test_page(f"{base_url}/users", "Users (redirect)"))
    test_results.append(test_page(f"{base_url}/users/list", "Users List"))
    test_results.append(test_page(f"{base_url}/users/add", "Add User Form"))
    
    # Test Buildings pages  
    test_results.append(test_page(f"{base_url}/buildings", "Buildings (redirect)"))
    test_results.append(test_page(f"{base_url}/buildings/list", "Buildings List"))
    test_results.append(test_page(f"{base_url}/buildings/add", "Add Building Form"))
    
    # Test API endpoints
    test_results.append(test_page(f"{base_url}/api/buildings", "Buildings API"))
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("🎉 Users and Buildings pages are working correctly!")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("🔧 Additional fixes may be needed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
