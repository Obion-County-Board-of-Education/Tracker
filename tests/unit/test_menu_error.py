#!/usr/bin/env python3
"""
Test the specific menu context issue
"""

import requests

def test_with_detailed_error():
    """Test and get detailed error information"""
    try:
        print("🧪 Testing /users/list with detailed error capture...")
        response = requests.get("http://localhost:8000/users/list", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        if response.status_code == 500:
            print("Content (first 500 chars):")
            print(response.text[:500])
            
            if 'menu_visibility' in response.text:
                print("❌ Confirmed: menu_visibility undefined error")
                return False
            else:
                print("❓ Different 500 error")
                return False
        elif response.status_code == 200:
            print("✅ Page loaded successfully!")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    test_with_detailed_error()
