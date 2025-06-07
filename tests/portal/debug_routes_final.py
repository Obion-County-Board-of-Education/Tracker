#!/usr/bin/env python3
"""
Check what routes are actually registered in the FastAPI app
"""

import requests

def get_openapi_routes():
    """Get all routes from OpenAPI spec"""
    try:
        response = requests.get("http://localhost:8000/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get('paths', {})
            print("🔍 REGISTERED ROUTES FROM OPENAPI:")
            print("=" * 50)
            for path, methods in paths.items():
                for method in methods.keys():
                    print(f"  {method.upper()} {path}")
            return True
        else:
            print(f"❌ Failed to get OpenAPI spec: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting OpenAPI routes: {e}")
        return False

def test_specific_routes():
    """Test specific routes we expect to exist"""
    routes_to_test = [
        "/users",
        "/users/list", 
        "/buildings",
        "/buildings/list",
        "/api/buildings",
        "/api/buildings/1/rooms"
    ]
    
    print("\n🧪 TESTING SPECIFIC ROUTES:")
    print("=" * 50)
    
    for route in routes_to_test:
        try:
            response = requests.get(f"http://localhost:8000{route}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {route}: HTTP 200 (OK)")
            elif response.status_code == 302:
                location = response.headers.get('location', 'unknown')
                print(f"↗️  {route}: HTTP 302 (Redirect to {location})")
            else:
                print(f"❌ {route}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {route}: ERROR - {str(e)[:50]}")

if __name__ == "__main__":
    print("🔍 ROUTE DEBUGGING TOOL")
    print("=" * 60)
    
    # Get all routes from OpenAPI
    openapi_success = get_openapi_routes()
    
    # Test specific routes
    test_specific_routes()
    
    print("\n" + "=" * 60)
    print("✅ Route debugging complete")
