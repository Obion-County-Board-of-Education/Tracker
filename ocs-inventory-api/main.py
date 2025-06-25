from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from ocs_shared_models import User, Building, Room
from ocs_shared_models.permissions import (
    require_inventory_read,
    require_inventory_write,
    require_admin,
    require_permission
)
from database import get_db, init_database
from auth_middleware import AuthMiddleware, get_current_user, has_permission

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Inventory API")

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

@app.get("/")
def root():
    return {"message": "OCS Inventory API is running."}

@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    return {"status": "healthy", "service": "inventory-api"}

# Inventory API Endpoints

@app.get("/api/inventory/items")
@require_inventory_read
def get_inventory_items(request: Request, db: Session = Depends(get_db)):
    """Get all inventory items"""
    return {"message": "Inventory items endpoint - requires read access", "user": get_current_user(request)}

@app.post("/api/inventory/items")
@require_inventory_write
def create_inventory_item(request: Request, db: Session = Depends(get_db)):
    """Create new inventory item"""
    return {"message": "Create inventory item endpoint - requires write access", "user": get_current_user(request)}

@app.get("/api/inventory/checkout")
@require_inventory_read
def get_checkouts(request: Request, db: Session = Depends(get_db)):
    """Get inventory checkouts"""
    return {"message": "Inventory checkouts endpoint - requires read access", "user": get_current_user(request)}

@app.post("/api/inventory/checkout")
@require_inventory_write
def checkout_item(request: Request, db: Session = Depends(get_db)):
    """Checkout inventory item"""
    return {"message": "Checkout item endpoint - requires write access", "user": get_current_user(request)}

@app.post("/api/inventory/admin/bulk-import")
@require_permission("inventory", "admin")
def bulk_import_inventory(request: Request, db: Session = Depends(get_db)):
    """Bulk import inventory items"""
    return {"message": "Bulk import endpoint - requires admin access", "user": get_current_user(request)}
