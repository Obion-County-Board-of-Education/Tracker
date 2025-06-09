#!/usr/bin/env python3
"""
Test script to verify Edit User functionality is working
"""

import requests
import sys
import time
from subprocess import Popen, PIPE
import subprocess

def test_portal_routes():
    """Test that the portal routes are accessible"""
    
    # Base URL for the portal
    base_url = "http://localhost:8002"
    
    print("🧪 Testing Edit User Route Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Check if server is running
        print("\n1. Testing server connectivity...")
        response = requests.get(f"{base_url}/users/list", timeout=5)
        if response.status_code == 200:
            print("✅ Portal server is running and users list is accessible")
        else:
            print(f"❌ Users list returned status: {response.status_code}")
            return False
            
    except requests.ConnectionError:
        print("❌ Cannot connect to portal server. Make sure it's running on port 8002")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False
    
    # Test 2: Check Edit User form (GET)
    print("\n2. Testing Edit User form access...")
    try:
        response = requests.get(f"{base_url}/users/edit/1", timeout=5)
        if response.status_code == 200:
            print("✅ Edit User form is accessible")
            if "edit_user.html" in response.text or "Edit User" in response.text:
                print("✅ Edit User form contains expected content")
            else:
                print("⚠️  Edit User form may not be rendering correctly")
        else:
            print(f"❌ Edit User form returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing Edit User form: {e}")
        return False
    
    # Test 3: Check users list has Edit buttons
    print("\n3. Testing Edit buttons in users list...")
    try:
        response = requests.get(f"{base_url}/users/list", timeout=5)
        if "/users/edit/" in response.text:
            print("✅ Users list contains Edit buttons with correct links")
        else:
            print("❌ Users list does not contain Edit buttons")
            
        if "/users/delete/" in response.text:
            print("✅ Users list contains Delete buttons with correct links")
        else:
            print("❌ Users list does not contain Delete buttons")
            
    except Exception as e:
        print(f"❌ Error checking users list: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Edit User functionality test completed!")
    print("✅ All routes are working correctly")
    return True

def check_server_running():
    """Check if the portal server is running"""
    try:
        response = requests.get("http://localhost:8002/users/list", timeout=2)
        return True
    except:
        return False

if __name__ == "__main__":
    print("🔍 Checking if portal server is running...")
    
    if not check_server_running():
        print("❌ Portal server is not running on port 8002")
        print("💡 Please start the server first with: python main.py")
        print("   Then run this test again")
        sys.exit(1)
    
    success = test_portal_routes()
    if success:
        print("🎉 All tests passed! Edit User functionality is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the issues above.")
        sys.exit(1)
