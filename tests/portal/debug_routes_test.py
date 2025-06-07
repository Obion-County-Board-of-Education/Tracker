"""
Debug script to check if the user and building routes are properly registered
"""
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI
from ocs_portal_py.user_building_routes import setup_user_building_routes

# Create a test app
app = FastAPI()

# Setup the routes
try:
    setup_user_building_routes(app)
    print("✅ Routes setup successful")
except Exception as e:
    print(f"❌ Routes setup failed: {e}")

# Check what routes are registered
print(f"\nTotal routes registered: {len(app.routes)}")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"  {route.path} ({route.methods})")
