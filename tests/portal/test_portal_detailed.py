import requests
import json

def test_portal_routes():
    base_url = "http://localhost:8003"
    
    print("Testing OCS Portal Routes...")
    print("=" * 50)
    
    # Test basic routing
    routes_to_test = [
        ("/", "Homepage"),
        ("/test-routing", "Test Route"),
        ("/users", "Users Redirect"),
        ("/users/list", "Users List"),
        ("/buildings", "Buildings Redirect"), 
        ("/buildings/list", "Buildings List")
    ]
    
    for route, description in routes_to_test:
        try:
            print(f"\nTesting {description} ({route})...")
            response = requests.get(f"{base_url}{route}", timeout=10, allow_redirects=False)
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 302:
                location = response.headers.get('location', 'No location header')
                print(f"  Redirect to: {location}")
            elif response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"  JSON Response: {json.dumps(data, indent=2)}")
                    except:
                        print(f"  Response length: {len(response.text)} characters")
                else:
                    print(f"  HTML Response length: {len(response.text)} characters")
                    if 'users' in route.lower() and 'user management' in response.text.lower():
                        print("  ✅ Users page loaded successfully")
                    elif 'buildings' in route.lower() and 'buildings management' in response.text.lower():
                        print("  ✅ Buildings page loaded successfully")
            else:
                print(f"  Error response: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Connection error: {e}")
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_portal_routes()
