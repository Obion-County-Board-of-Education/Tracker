#!/usr/bin/env python3

import requests
import json

def test_export_routes():
    base_url = "http://localhost:8003"
    
    # Test regular export routes
    routes_to_test = [
        "/api/tickets/tech/export",
        "/api/tickets/maintenance/export", 
        "/api/tickets/tech/export_for_import",
        "/api/tickets/maintenance/export_for_import",
        "/api/test/simple"
    ]
    
    print("Testing export routes availability:")
    print("=" * 50)
    
    for route in routes_to_test:
        try:
            url = f"{base_url}{route}"
            print(f"\nTesting: {route}")
            response = requests.get(url, timeout=5)
            print(f"Status: {response.status_code}")
            if response.status_code == 404:
                print(f"❌ Route NOT FOUND: {route}")
            elif response.status_code == 200:
                print(f"✅ Route FOUND: {route}")
                # Check if it's a CSV response
                if 'text/csv' in response.headers.get('content-type', ''):
                    print(f"   Content-Type: CSV (correct)")
                else:
                    print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            else:
                print(f"⚠️  Route exists but returned {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error testing {route}: {e}")
    
    # Get OpenAPI spec to see all registered routes
    print("\n" + "=" * 50)
    print("Checking OpenAPI spec for all registered routes:")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get('paths', {})
            
            print(f"\nTotal registered routes: {len(paths)}")
            export_routes = [path for path in paths.keys() if 'export' in path]
            print(f"Export routes found in spec: {len(export_routes)}")
            
            for route in export_routes:
                print(f"  - {route}")
                
            if '/api/tickets/tech/export_for_import' not in paths:
                print("❌ /api/tickets/tech/export_for_import NOT in OpenAPI spec")
            else:
                print("✅ /api/tickets/tech/export_for_import found in OpenAPI spec")
                
            if '/api/tickets/maintenance/export_for_import' not in paths:
                print("❌ /api/tickets/maintenance/export_for_import NOT in OpenAPI spec")
            else:
                print("✅ /api/tickets/maintenance/export_for_import found in OpenAPI spec")
        else:
            print(f"Failed to get OpenAPI spec: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error getting OpenAPI spec: {e}")

if __name__ == "__main__":
    test_export_routes()
