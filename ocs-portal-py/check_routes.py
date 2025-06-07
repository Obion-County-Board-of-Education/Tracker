#!/usr/bin/env python3
"""Check what routes are registered in the FastAPI app"""

from main import app

print("🔍 Checking registered routes:")
print("=" * 50)

users_list_found = False
buildings_list_found = False

for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ', '.join(route.methods) if route.methods else 'N/A'
        print(f"{route.path} ({methods})")
        
        if route.path == '/users/list':
            users_list_found = True
        if route.path == '/buildings/list':
            buildings_list_found = True

print("=" * 50)
print(f"Total routes: {len(app.routes)}")
print(f"✅ /users/list found: {users_list_found}")
print(f"✅ /buildings/list found: {buildings_list_found}")

if not users_list_found or not buildings_list_found:
    print("❌ Missing routes detected!")
else:
    print("✅ All expected routes found!")
