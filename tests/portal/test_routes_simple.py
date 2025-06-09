import requests

try:
    # Get OpenAPI spec
    response = requests.get('http://localhost:8001/openapi.json')
    if response.status_code == 200:
        spec = response.json()
        paths = spec.get('paths', {})
        
        # Find all routes containing 'tech'
        tech_routes = [path for path in paths.keys() if 'tech' in path]
        
        print("All registered tech routes:")
        for route in sorted(tech_routes):
            methods = list(paths[route].keys())
            print(f"  {route} - {methods}")
        
        # Check specifically for export routes
        export_routes = [path for path in paths.keys() if 'export' in path]
        print(f"\nAll export routes:")
        for route in sorted(export_routes):
            methods = list(paths[route].keys())
            print(f"  {route} - {methods}")
            
        # Test the underscore route
        print(f"\nTesting export_for_import route:")
        test_response = requests.get('http://localhost:8001/api/tickets/tech/export_for_import')
        print(f"Status: {test_response.status_code}")
        if test_response.status_code != 200:
            print(f"Error: {test_response.text}")
    else:
        print(f"Failed to get OpenAPI spec: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
