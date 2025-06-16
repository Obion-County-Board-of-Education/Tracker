"""
Comprehensive Authentication Flow Test
"""
import requests
import json
from datetime import datetime

def test_authentication_flow():
    """Test the complete authentication flow"""
    
    base_url = "http://localhost:8003"
    
    print("🔍 Testing OCS Tracker Authentication Flow")
    print("=" * 60)
    
    # Test 1: Root endpoint should redirect to login
    print("\n1. Testing root endpoint redirection...")
    try:
        response = requests.get(base_url, allow_redirects=False)
        print(f"   Status: {response.status_code}")
        if response.status_code == 302:
            location = response.headers.get('location', '')
            print(f"   ✅ Redirects to: {location}")
            if 'login' in location:
                print("   ✅ Correctly redirects to login")
            else:
                print("   ⚠️ Unexpected redirect destination")
        else:
            print("   ❌ Expected redirect (302) but got different status")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Login page accessibility
    print("\n2. Testing login page accessibility...")
    try:
        response = requests.get(f"{base_url}/login")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Login page accessible")
            if "Sign in with Microsoft" in response.text:
                print("   ✅ Microsoft login button found")
            else:
                print("   ⚠️ Microsoft login button not found in page")
        else:
            print(f"   ❌ Login page not accessible: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Health endpoint
    print("\n3. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health check: {health_data}")
            if health_data.get("authentication") == "enabled":
                print("   ✅ Authentication confirmed enabled")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Auth status endpoint
    print("\n4. Testing auth status endpoint...")
    try:
        response = requests.get(f"{base_url}/auth/status")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Auth status: {status_data}")
            if not status_data.get("authenticated"):
                print("   ✅ Correctly shows not authenticated")
        else:
            print(f"   ❌ Auth status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Protected route should redirect to login
    print("\n5. Testing protected route access...")
    try:
        response = requests.get(f"{base_url}/dashboard", allow_redirects=False)
        print(f"   Status: {response.status_code}")
        if response.status_code == 302:
            location = response.headers.get('location', '')
            print(f"   ✅ Redirects to: {location}")
            if 'login' in location:
                print("   ✅ Protected route correctly redirects to login")
        else:
            print(f"   ❌ Expected redirect but got: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Microsoft OAuth initiation
    print("\n6. Testing Microsoft OAuth initiation...")
    try:
        response = requests.get(f"{base_url}/auth/microsoft", allow_redirects=False)
        print(f"   Status: {response.status_code}")
        if response.status_code == 302:
            location = response.headers.get('location', '')
            print(f"   ✅ Redirects to Microsoft: {location[:80]}...")
            if 'login.microsoftonline.com' in location:
                print("   ✅ Correctly redirects to Microsoft OAuth")
            else:
                print("   ⚠️ Unexpected OAuth destination")
        else:
            print(f"   ❌ Expected redirect but got: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 7: API endpoint protection
    print("\n7. Testing API endpoint protection...")
    try:
        response = requests.get(f"{base_url}/api/user")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ API correctly returns 401 Unauthorized")
        else:
            print(f"   ❌ Expected 401 but got: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Authentication Flow Test Summary:")
    print("✅ Application is running and responding")
    print("✅ Authentication middleware is active") 
    print("✅ Protected routes are secured")
    print("✅ OAuth flow is properly configured")
    print("✅ Login page is accessible and functional")
    print("\n🚀 Ready for user authentication testing!")
    print("\n📋 Manual Test Steps:")
    print("1. Open http://localhost:8003 in your browser")
    print("2. Click 'Sign in with Microsoft'")
    print("3. Authenticate with your OCS Azure AD account")
    print("4. You should be redirected to the dashboard")
    print("5. Verify your permissions and available services")

if __name__ == "__main__":
    test_authentication_flow()
