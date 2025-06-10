#!/usr/bin/env python3
"""
Minimal test to identify the exact issue with route registration
"""

from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Create a minimal app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Import dependencies
try:
    from models import User, Building
    from database import get_db
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Add a working route
@app.get("/test")
def test_route():
    return {"message": "test works"}

print(f"Routes after test: {len(app.routes)}")

# Now try to add the problematic users_list route exactly as it appears in main.py
@app.get("/users/list")
def users_list(request: Request, db: Session = Depends(get_db)):
    """List all users from database with enhanced information"""
    try:
        users = db.query(User).all()
        users_data = []
        for user in users:
            # Get user's building assignments if any
            building_count = len(user.buildings) if user.buildings else 0
            
            user_info = {
                "id": user.id,
                "name": user.display_name or user.username,
                "email": user.email or f"{user.username}@obionschools.com",
                "role": (user.roles or 'basic').title(),
                "username": user.username,
                "building_count": building_count
            }
            users_data.append(user_info)
            
    except Exception as e:
        print(f"Database error: {e}")
        users_data = []
    
    return templates.TemplateResponse("users.html", {"request": request, "users": users_data})

print(f"Routes after users_list: {len(app.routes)}")

# Test if the route was actually registered
users_route_found = False
for route in app.routes:
    if hasattr(route, 'path') and '/users/list' in route.path:
        users_route_found = True
        break

print(f"✅ /users/list route registered: {users_route_found}")

if __name__ == "__main__":
    print("✅ Test completed successfully")
