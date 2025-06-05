#!/usr/bin/env python3
"""
Test script to isolate the exact error in users_list function definition
"""

from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User
from database import get_db

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Test the exact users_list function definition
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

print("✅ Test function definition successful")
print(f"Routes: {len(app.routes)}")
