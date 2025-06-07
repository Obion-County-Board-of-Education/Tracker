#!/usr/bin/env python3

# Test script to verify route registration
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ocs_shared_models import User, Building
from database import get_db

app = FastAPI()
templates = Jinja2Templates(directory="templates")

print("Starting route registration test...")

@app.get("/")
def home():
    return {"message": "home"}

print("Home route registered")

@app.get("/users/list")
def users_list(request: Request, db: Session = Depends(get_db)):
    """List all users"""
    try:
        users = db.query(User).all()
        users_data = []
        for user in users:
            user_info = {
                "id": user.id,
                "name": user.display_name or user.username,
                "email": user.email or f"{user.username}@obionschools.com",
                "role": (user.roles or 'basic').title(),
                "username": user.username,
            }
            users_data.append(user_info)
    except Exception as e:
        print(f"Database error: {e}")
        users_data = [{"id": 1, "name": "Test User", "email": "test@test.com", "role": "Admin", "username": "test"}]
    
    return templates.TemplateResponse("users.html", {"request": request, "users": users_data})

print("Users route registered")

@app.get("/buildings/list")
def buildings_list(request: Request, db: Session = Depends(get_db)):
    """List all buildings"""
    try:
        buildings = db.query(Building).all()
        buildings_data = []
        for building in buildings:
            building_info = {
                "id": building.id,
                "name": building.name,
            }
            buildings_data.append(building_info)
    except Exception as e:
        print(f"Database error: {e}")
        buildings_data = [{"id": 1, "name": "Test Building"}]
    
    return templates.TemplateResponse("buildings.html", {"request": request, "buildings": buildings_data})

print("Buildings route registered")

if __name__ == "__main__":
    print(f"Total routes: {len(app.routes)}")
    for route in app.routes:
        print(f"  {route.path}")
