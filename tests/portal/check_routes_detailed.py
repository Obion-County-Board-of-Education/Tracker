import requests
import json

try:
    response = requests.get('http://localhost:8000/openapi.json')
    if response.status_code == 200:
        spec = response.json()
        
        # Print all paths
        print("=== ALL REGISTERED ROUTES ===")
        for path in sorted(spec.get('paths', {}).keys()):
            methods = list(spec['paths'][path].keys())
            print(f"{path} - {methods}")
        
        # Check specifically for our routes
        print(f"\n=== LOOKING FOR EXPORT ROUTES ===")
        paths = spec.get('paths', {})
        
        # Look for any route containing 'export'
        export_routes = {path: methods for path, methods in paths.items() if 'export' in path}
        if export_routes:
            for path, details in export_routes.items():
                methods = list(details.keys())
                print(f"FOUND: {path} - {methods}")
        else:
            print("NO EXPORT ROUTES FOUND!")
            
        # Look for our specific routes
        target_routes = [
            '/api/tickets/tech/export_for_import',
            '/api/tickets/maintenance/export_for_import',
            '/api/tickets/tech/export-for-import',
            '/api/tickets/maintenance/export-for-import'
        ]
        
        print(f"\n=== CHECKING TARGET ROUTES ===")
        for route in target_routes:
            if route in paths:
                print(f"✅ FOUND: {route}")
            else:
                print(f"❌ NOT FOUND: {route}")
                
    else:
        print(f"Failed to get OpenAPI spec: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
