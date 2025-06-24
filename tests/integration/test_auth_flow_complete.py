#!/usr/bin/env python3
"""
Complete authentication flow test
"""
import requests
import sys
from urllib.parse import urlparse, parse_qs

def test_complete_auth_flow():
    """Test the complete authentication flow with next parameter"""
    base_url = "http://localhost:8003"
    
    print("=== Testing Complete Authentication Flow ===")
    
    # Step 1: Try to access a protected route
    print("\n1. Testing access to protected route without authentication...")
    try:
        response = requests.get(f"{base_url}/tickets/tech/open", allow_redirects=False)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 302:
            redirect_location = response.headers.get('Location', '')
            print(f"   Redirect to: {redirect_location}")
            
            # Check if the redirect includes the next parameter
            if 'next=' in redirect_location:
                parsed_url = urlparse(redirect_location)
                query_params = parse_qs(parsed_url.query)
                next_param = query_params.get('next', [None])[0]
                print(f"   ✅ Next parameter found: {next_param}")
                
                # Step 2: Follow the redirect to login page
                print("\n2. Testing login page with next parameter...")
                full_login_url = f"{base_url}{redirect_location}"
                login_response = requests.get(full_login_url)
                print(f"   Login page status: {login_response.status_code}")
                
                if login_response.status_code == 200:
                    # Check if the login page contains the Microsoft auth link with next parameter
                    if 'microsoft' in login_response.text.lower():
                        print("   ✅ Login page loaded successfully")
                        
                        # Extract the Microsoft auth URL from the page
                        import re
                        auth_link_match = re.search(r'href="(/auth/microsoft[^"]*)"', login_response.text)
                        if auth_link_match:
                            auth_link = auth_link_match.group(1)
                            print(f"   Microsoft auth link: {auth_link}")
                            
                            if 'next=' in auth_link:
                                print("   ✅ Next parameter is being passed to Microsoft auth")
                                
                                # Step 3: Test Microsoft auth initiation
                                print("\n3. Testing Microsoft OAuth initiation...")
                                session = requests.Session()  # Use session to maintain cookies
                                
                                # First visit the login page to get session cookie
                                session.get(full_login_url)
                                
                                # Then try the Microsoft auth endpoint
                                microsoft_auth_response = session.get(
                                    f"{base_url}{auth_link}", 
                                    allow_redirects=False
                                )
                                print(f"   Microsoft auth status: {microsoft_auth_response.status_code}")
                                
                                if microsoft_auth_response.status_code == 302:
                                    auth_redirect = microsoft_auth_response.headers.get('Location', '')
                                    if 'login.microsoftonline.com' in auth_redirect:
                                        print("   ✅ Successfully redirected to Microsoft OAuth")
                                        print("   🔗 OAuth URL would be:", auth_redirect[:100] + "...")
                                        
                                        print("\n=== MANUAL TESTING REQUIRED ===")
                                        print("To complete the test:")
                                        print(f"1. Open: {full_login_url}")
                                        print("2. Click 'Sign in with Microsoft'")
                                        print("3. Complete OAuth flow")
                                        print("4. Verify you land on the original page:", next_param)
                                        
                                        return True
                                    else:
                                        print(f"   ❌ Unexpected redirect: {auth_redirect}")
                                else:
                                    print(f"   ❌ Unexpected response from Microsoft auth")
                            else:
                                print("   ❌ Next parameter missing from Microsoft auth link")
                        else:
                            print("   ❌ Could not find Microsoft auth link in login page")
                    else:
                        print("   ❌ Login page doesn't contain Microsoft auth option")
                else:
                    print(f"   ❌ Login page failed to load: {login_response.status_code}")
            else:
                print("   ❌ No next parameter in redirect")
        else:
            print(f"   ❌ Expected redirect (302), got {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error during test: {e}")
        return False
    
    return False

def test_session_storage():
    """Test if session storage is working for next parameter"""
    base_url = "http://localhost:8003"
    
    print("\n=== Testing Session Storage ===")
    
    try:
        session = requests.Session()
        
        # Test storing and retrieving session data
        print("1. Testing session persistence...")
        
        # Make a request that should set up a session
        response = session.get(f"{base_url}/auth/login?next=/test/page")
        
        if response.status_code == 200:
            print("   ✅ Login page accessible")
            
            # Check if session cookies are set
            cookies = session.cookies
            if cookies:
                print(f"   ✅ Session cookies present: {list(cookies.keys())}")
            else:
                print("   ⚠️  No session cookies found")
                
        return True
        
    except Exception as e:
        print(f"   ❌ Session test error: {e}")
        return False

if __name__ == "__main__":
    print("Testing OCS Portal Authentication Flow")
    print("=====================================")
    
    # Test the complete flow
    flow_success = test_complete_auth_flow()
    
    # Test session storage
    session_success = test_session_storage()
    
    if flow_success:
        print("\n✅ Authentication flow test completed successfully")
        print("Manual testing required to verify OAuth callback")
    else:
        print("\n❌ Authentication flow test failed")
        
    print("\nNote: Complete the manual steps above to test the full flow")
