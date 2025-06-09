#!/usr/bin/env python3
"""Debug the FastAPI route registration"""

import requests
import json

def test_fastapi_routes():
    """Test what routes are actually registered in FastAPI"""
    
    base_url = "http://localhost:8000"
    
    # Try to get OpenAPI docs to see registered routes
    print("Getting OpenAPI spec to see registered routes...")
    try:
        response = requests.get(f"{base_url}/openapi.json")
        print(f"OpenAPI spec - Status: {response.status_code}")
        
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get('paths', {})
            
            print("\nRegistered tech ticket routes:")
            for path, methods in paths.items():
                if '/tickets/tech' in path:
                    for method, details in methods.items():
                        print(f"  {method.upper()} {path}")
                        
            # Check specifically for our export-for-import route
            export_route = "/api/tickets/tech/export-for-import"
            if export_route in paths:
                print(f"\n✅ Found export-for-import route: {export_route}")
                if 'get' in paths[export_route]:
                    print("✅ GET method is registered for export-for-import")
                else:
                    print("❌ GET method NOT registered for export-for-import")
            else:
                print(f"\n❌ export-for-import route NOT found: {export_route}")
                
        else:
            print(f"❌ Failed to get OpenAPI spec: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API - is Docker running?")
        return False
    except Exception as e:
        print(f"❌ Error testing routes: {e}")
        return False
    
    # Also test the actual routes
    print("\n" + "="*50)
    print("Testing actual route access:")
    
    # Test working export route
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export")
        print(f"Regular export route - Status: {response.status_code}")
    except Exception as e:
        print(f"Regular export route - Error: {e}")
    
    # Test problematic export-for-import route
    try:
        response = requests.get(f"{base_url}/api/tickets/tech/export-for-import")
        print(f"Export-for-import route - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Export-for-import route - Error: {e}")
    
    return True

if __name__ == "__main__":
    test_fastapi_routes()
