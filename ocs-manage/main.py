from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from ocs_shared_models import User, Building, Room, UserRole
from ocs_shared_models.permissions import (
    require_admin,
    require_super_admin,
    require_permission
)
from database import get_db, init_database
from auth_middleware import AuthMiddleware, get_current_user, has_permission

# Initialize database on startup
init_database()

app = FastAPI(
    title="OCS Manage API",
    description="Management and administration API for OCS services",
    version="1.0.0"
)

# Configure CORS for cross-service communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware with excluded paths
app.add_middleware(
    AuthMiddleware,
    exclude_paths=[
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc"
    ]
)

# Pydantic models for API responses
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class BuildingResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class RoomResponse(BaseModel):
    id: int
    name: str
    building_id: int
    room_type: Optional[str] = None
    
    class Config:
        from_attributes = True

# Health check endpoint
@app.get("/", tags=["Health"])
def read_root():
    return {
        "service": "OCS Manage API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

# User management endpoints
@app.get("/api/users", response_model=List[UserResponse], tags=["Users"])
@require_admin
def get_users(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users with pagination"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
@require_admin
def get_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Building management endpoints
@app.get("/api/buildings", response_model=List[BuildingResponse], tags=["Buildings"])
@require_admin
def get_buildings(request: Request, db: Session = Depends(get_db)):
    """Get all buildings"""
    buildings = db.query(Building).all()
    return buildings

@app.get("/api/buildings/{building_id}", response_model=BuildingResponse, tags=["Buildings"])
@require_admin
def get_building(request: Request, building_id: int, db: Session = Depends(get_db)):
    """Get a specific building by ID"""
    building = db.query(Building).filter(Building.id == building_id).first()
    if building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    return building

@app.get("/api/buildings/{building_id}/rooms", response_model=List[RoomResponse], tags=["Buildings"])
@require_admin
def get_building_rooms(request: Request, building_id: int, db: Session = Depends(get_db)):
    """Get all rooms for a specific building"""
    building = db.query(Building).filter(Building.id == building_id).first()
    if building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    
    rooms = db.query(Room).filter(Room.building_id == building_id).all()
    return rooms

# System management endpoints
@app.get("/api/system/stats", tags=["System"])
@require_super_admin
def get_system_stats(request: Request, db: Session = Depends(get_db)):
    """Get system statistics"""
    user_count = db.query(User).count()
    building_count = db.query(Building).count()
    room_count = db.query(Room).count()
    
    return {
        "users": user_count,
        "buildings": building_count,
        "rooms": room_count,
        "timestamp": datetime.now().isoformat()
    }

# Additional system management endpoints
@app.post("/api/logs/clear", tags=["System"])
@require_super_admin
def clear_logs(request: Request):
    """Clear all system logs"""
    # Placeholder implementation
    return {"success": True, "message": "Logs cleared successfully"}

@app.get("/api/system/settings", tags=["System"])
@require_super_admin
def get_system_settings(request: Request):
    """Get system settings"""
    # Placeholder implementation
    return {
        "maintenance_mode": False,
        "max_upload_size": "10MB",
        "session_timeout": 3600,
        "auto_backup": True,
        "backup_interval": 24
    }

@app.put("/api/system/settings", tags=["System"])
@require_super_admin
def update_system_settings(request: Request, settings: dict):
    """Update system settings"""
    # Placeholder implementation
    return {"success": True, "message": "Settings updated successfully"}

@app.post("/api/maintenance/run", tags=["System"])
@require_super_admin
def run_maintenance(request: Request):
    """Run system maintenance tasks"""
    # Placeholder implementation
    return {"success": True, "message": "Maintenance completed successfully"}

@app.post("/api/search/rebuild", tags=["System"])
@require_super_admin
def rebuild_search_index(request: Request):
    """Rebuild search index"""
    # Placeholder implementation
    return {"success": True, "message": "Search index rebuilt successfully"}

@app.post("/api/database/optimize", tags=["System"])
@require_super_admin
def optimize_databases(request: Request):
    """Optimize all databases"""
    # Placeholder implementation
    return {"success": True, "message": "Database optimization completed successfully"}

@app.post("/api/data/import", tags=["System"])
def import_data():
    """Import data from file"""
    # Placeholder implementation
    return {"success": True, "message": "Data imported successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
