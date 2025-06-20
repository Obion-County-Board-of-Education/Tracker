from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from ocs_shared_models import User, Building, Room, UserRole, InventoryItem, InventoryCheckout
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
        "/redoc",
        "/inventory"
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

# Pydantic models for inventory
class InventoryItemResponse(BaseModel):
    id: int
    tag: str
    type: str
    brand: str
    model: str
    serial: str
    po_number: str
    price: float
    purchase_date: datetime
    funds: str
    vendor: str
    school: str
    room: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class InventoryItemCreate(BaseModel):
    tag: str
    type: str
    brand: str
    model: str
    serial: str
    po_number: str
    price: float
    purchase_date: datetime
    funds: str
    vendor: str
    school: str
    room: str

class InventoryCheckoutResponse(BaseModel):
    id: int
    item_id: int
    checkout_type: str
    checked_out_by: str
    checked_out_at: datetime
    expected_return_date: Optional[datetime]
    notes: Optional[str]
    returned_at: Optional[datetime]
    returned_by: Optional[str]
    is_active: bool
    
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

# ===============================
# INVENTORY MANAGEMENT ENDPOINTS
# ===============================

@app.get("/inventory", tags=["Inventory"])
def inventory_home():
    """Inventory service home page"""
    return {"service": "Inventory Management", "status": "active", "message": "Inventory functionality merged with Management API"}

@app.get("/api/inventory", response_model=List[InventoryItemResponse], tags=["Inventory"])
@require_permission("inventory_access")
def get_inventory_items(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    school: Optional[str] = None,
    sort: Optional[str] = "newest",
    db: Session = Depends(get_db)
):
    """Get inventory items with filtering and sorting"""
    query = db.query(InventoryItem)
    
    if school:
        query = query.filter(InventoryItem.school == school)
    
    # Apply sorting
    if sort == "oldest":
        query = query.order_by(InventoryItem.created_at.asc())
    elif sort == "numerical":
        query = query.order_by(InventoryItem.tag)
    elif sort == "alphabetical":
        query = query.order_by(InventoryItem.type, InventoryItem.brand)
    else:  # newest (default)
        query = query.order_by(InventoryItem.created_at.desc())
    
    items = query.offset(skip).limit(limit).all()
    return items

@app.get("/api/inventory/{item_id}", response_model=InventoryItemResponse, tags=["Inventory"])
@require_permission("inventory_access")
def get_inventory_item(request: Request, item_id: int, db: Session = Depends(get_db)):
    """Get specific inventory item"""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item

@app.post("/api/inventory", tags=["Inventory"])
@require_permission("inventory_write")
def create_inventory_item(request: Request, item: InventoryItemCreate, db: Session = Depends(get_db)):
    """Create new inventory item"""
    db_item = InventoryItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"success": True, "item_id": db_item.id, "message": "Inventory item created successfully"}

@app.put("/api/inventory/{item_id}", tags=["Inventory"])
@require_permission("inventory_write")
def update_inventory_item(request: Request, item_id: int, item: InventoryItemCreate, db: Session = Depends(get_db)):
    """Update inventory item"""
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    
    db.commit()
    return {"success": True, "message": "Inventory item updated successfully"}

@app.delete("/api/inventory/{item_id}", tags=["Inventory"])
@require_permission("inventory_admin")
def delete_inventory_item(request: Request, item_id: int, db: Session = Depends(get_db)):
    """Delete inventory item"""
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    db.delete(db_item)
    db.commit()
    return {"success": True, "message": "Inventory item deleted successfully"}

@app.post("/api/inventory/checkout", tags=["Inventory"])
@require_permission("inventory_write")
def checkout_device(request: Request, checkout_data: dict, db: Session = Depends(get_db)):
    """Checkout device to location or user"""
    checkout = InventoryCheckout(**checkout_data)
    db.add(checkout)
    db.commit()
    return {"success": True, "checkout_id": checkout.id, "message": "Device checked out successfully"}

@app.put("/api/inventory/checkout/{checkout_id}/return", tags=["Inventory"])
@require_permission("inventory_write")
def checkin_device(request: Request, checkout_id: int, return_data: dict, db: Session = Depends(get_db)):
    """Check in device from checkout"""
    checkout = db.query(InventoryCheckout).filter(InventoryCheckout.id == checkout_id).first()
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    
    checkout.returned_at = datetime.now()
    checkout.returned_by = return_data.get("returned_by")
    checkout.return_condition = return_data.get("condition")
    checkout.return_notes = return_data.get("notes")
    checkout.is_active = False
    
    db.commit()
    return {"success": True, "message": "Device checked in successfully"}

@app.get("/api/inventory/checkout/history", response_model=List[InventoryCheckoutResponse], tags=["Inventory"])
@require_permission("inventory_access")
def get_checkout_history(request: Request, item_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get checkout history"""
    query = db.query(InventoryCheckout)
    if item_id:
        query = query.filter(InventoryCheckout.item_id == item_id)
    
    checkouts = query.order_by(InventoryCheckout.checked_out_at.desc()).all()
    return checkouts

@app.get("/api/inventory/search", response_model=List[InventoryItemResponse], tags=["Inventory"])
@require_permission("inventory_access")
def search_inventory(
    request: Request,
    tag: Optional[str] = None,
    serial: Optional[str] = None,
    po_number: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search inventory by tag, serial, or PO number"""
    query = db.query(InventoryItem)
    
    if tag:
        query = query.filter(InventoryItem.tag.ilike(f"%{tag}%"))
    if serial:
        query = query.filter(InventoryItem.serial.ilike(f"%{serial}%"))
    if po_number:
        query = query.filter(InventoryItem.po_number.ilike(f"%{po_number}%"))
    
    items = query.limit(50).all()  # Limit search results
    return items

@app.get("/api/inventory/stats", tags=["Inventory"])
@require_permission("inventory_access") 
def get_inventory_stats(request: Request, db: Session = Depends(get_db)):
    """Get inventory statistics"""
    total_items = db.query(InventoryItem).count()
    active_checkouts = db.query(InventoryCheckout).filter(InventoryCheckout.is_active == True).count()
    
    # Get counts by school
    school_counts = db.query(InventoryItem.school, db.func.count(InventoryItem.id)).group_by(InventoryItem.school).all()
    
    return {
        "total_items": total_items,
        "active_checkouts": active_checkouts,
        "school_distribution": dict(school_counts)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
