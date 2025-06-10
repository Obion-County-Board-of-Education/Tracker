import requests
import json

# Test with proper error handling
try:
    print("Testing export_for_import route with detailed error info...")
    response = requests.get("http://localhost:8000/api/tickets/tech/export_for_import", timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 422:
        try:
            error_detail = response.json()
            print(f"Validation Error Details: {json.dumps(error_detail, indent=2)}")
        except:
            print("Could not parse error response as JSON")
            
except Exception as e:
    print(f"Request Error: {e}")

print("\n" + "="*50)

# Test OpenAPI spec to see if route is registered
try:
    print("Checking OpenAPI spec...")
    response = requests.get("http://localhost:8000/openapi.json", timeout=10)
    if response.status_code == 200:
        spec = response.json()
        paths = spec.get('paths', {})
        
        export_paths = [path for path in paths.keys() if 'export' in path.lower()]
        print(f"Export routes in OpenAPI spec:")
        for path in export_paths:
            print(f"  - {path}")
            
        if '/api/tickets/tech/export_for_import' in paths:
            print(f"\n✅ export_for_import route IS registered in OpenAPI")
            route_info = paths['/api/tickets/tech/export_for_import']
            print(f"Route details: {json.dumps(route_info, indent=2)}")
        else:
            print(f"\n❌ export_for_import route NOT in OpenAPI spec")
    else:
        print(f"Failed to get OpenAPI spec: {response.status_code}")
except Exception as e:
    print(f"OpenAPI Error: {e}")
