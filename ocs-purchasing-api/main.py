import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import sys
import os

# Add the parent directory to the Python path to import shared models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ocs_shared_models import User, Building, Room, Requisition, PurchaseOrder
from ocs_shared_models.timezone_utils import central_now, format_central_time
from database import get_db, init_database

# Initialize database on startup
init_database()

app = FastAPI(
    title="OCS Purchasing API",
    description="Requisitions and Purchase Orders API for OCS services",
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

# Pydantic models for API requests/responses
class RequisitionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    department: str
    requested_by: str
    estimated_cost: Optional[str] = None
    justification: Optional[str] = None
    priority: str = "normal"
    building_id: Optional[int] = None

class RequisitionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    department: str
    requested_by: str
    status: str
    estimated_cost: Optional[str]
    justification: Optional[str]
    priority: str
    building_id: Optional[int]
    approved_by: Optional[str]
    approved_at: Optional[str]
    created_at: str
    updated_at: Optional[str]

class PurchaseOrderCreate(BaseModel):
    po_number: str
    requisition_id: Optional[int] = None
    vendor_name: str
    vendor_contact: Optional[str] = None
    total_amount: Optional[str] = None
    description: Optional[str] = None
    delivery_address: Optional[str] = None
    created_by: str

class PurchaseOrderResponse(BaseModel):
    id: int
    po_number: str
    requisition_id: Optional[int]
    vendor_name: str
    vendor_contact: Optional[str]
    total_amount: Optional[str]
    status: str
    description: Optional[str]
    delivery_address: Optional[str]
    created_by: str
    approved_by: Optional[str]
    sent_date: Optional[str]
    received_date: Optional[str]
    created_at: str
    updated_at: Optional[str]

# Health check endpoint
@app.get("/", tags=["Health"])
def read_root():
    return {"message": "OCS Purchasing API is running", "status": "healthy"}

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for service monitoring"""
    return {"status": "healthy", "service": "ocs-purchasing-api", "timestamp": central_now().isoformat()}

# Requisitions endpoints
@app.get("/api/requisitions", response_model=List[RequisitionResponse], tags=["Requisitions"])
def get_requisitions(
    status: Optional[str] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db)
):
    """Get all requisitions with optional filtering"""
    query = db.query(Requisition)
    
    if status:
        query = query.filter(Requisition.status == status)
    if department:
        query = query.filter(Requisition.department == department)
    if priority:
        query = query.filter(Requisition.priority == priority)
    
    requisitions = query.order_by(Requisition.created_at.desc()).all()
    
    return [
        RequisitionResponse(
            id=req.id,
            title=req.title,
            description=req.description,
            department=req.department,
            requested_by=req.requested_by,
            status=req.status,
            estimated_cost=req.estimated_cost,
            justification=req.justification,
            priority=req.priority,
            building_id=req.building_id,
            approved_by=req.approved_by,
            approved_at=format_central_time(req.approved_at) if req.approved_at else None,
            created_at=format_central_time(req.created_at),
            updated_at=format_central_time(req.updated_at) if req.updated_at else None
        )
        for req in requisitions
    ]

@app.post("/api/requisitions", response_model=RequisitionResponse, tags=["Requisitions"])
def create_requisition(requisition: RequisitionCreate, db: Session = Depends(get_db)):
    """Create a new requisition"""
    db_requisition = Requisition(
        title=requisition.title,
        description=requisition.description,
        department=requisition.department,
        requested_by=requisition.requested_by,
        estimated_cost=requisition.estimated_cost,
        justification=requisition.justification,
        priority=requisition.priority,
        building_id=requisition.building_id
    )
    
    db.add(db_requisition)
    db.commit()
    db.refresh(db_requisition)
    
    return RequisitionResponse(
        id=db_requisition.id,
        title=db_requisition.title,
        description=db_requisition.description,
        department=db_requisition.department,
        requested_by=db_requisition.requested_by,
        status=db_requisition.status,
        estimated_cost=db_requisition.estimated_cost,
        justification=db_requisition.justification,
        priority=db_requisition.priority,
        building_id=db_requisition.building_id,
        approved_by=db_requisition.approved_by,
        approved_at=format_central_time(db_requisition.approved_at) if db_requisition.approved_at else None,
        created_at=format_central_time(db_requisition.created_at),
        updated_at=format_central_time(db_requisition.updated_at) if db_requisition.updated_at else None
    )

@app.get("/api/requisitions/{requisition_id}", response_model=RequisitionResponse, tags=["Requisitions"])
def get_requisition(requisition_id: int, db: Session = Depends(get_db)):
    """Get a specific requisition by ID"""
    requisition = db.query(Requisition).filter(Requisition.id == requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    
    return RequisitionResponse(
        id=requisition.id,
        title=requisition.title,
        description=requisition.description,
        department=requisition.department,
        requested_by=requisition.requested_by,
        status=requisition.status,
        estimated_cost=requisition.estimated_cost,
        justification=requisition.justification,
        priority=requisition.priority,
        building_id=requisition.building_id,
        approved_by=requisition.approved_by,
        approved_at=format_central_time(requisition.approved_at) if requisition.approved_at else None,
        created_at=format_central_time(requisition.created_at),
        updated_at=format_central_time(requisition.updated_at) if requisition.updated_at else None
    )

@app.put("/api/requisitions/{requisition_id}/approve", response_model=RequisitionResponse, tags=["Requisitions"])
def approve_requisition(requisition_id: int, approved_by: str, db: Session = Depends(get_db)):
    """Approve a requisition"""
    requisition = db.query(Requisition).filter(Requisition.id == requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    
    requisition.status = "approved"
    requisition.approved_by = approved_by
    requisition.approved_at = central_now()
    requisition.updated_at = central_now()
    
    db.commit()
    db.refresh(requisition)
    
    return RequisitionResponse(
        id=requisition.id,
        title=requisition.title,
        description=requisition.description,
        department=requisition.department,
        requested_by=requisition.requested_by,
        status=requisition.status,
        estimated_cost=requisition.estimated_cost,
        justification=requisition.justification,
        priority=requisition.priority,
        building_id=requisition.building_id,
        approved_by=requisition.approved_by,
        approved_at=format_central_time(requisition.approved_at) if requisition.approved_at else None,
        created_at=format_central_time(requisition.created_at),
        updated_at=format_central_time(requisition.updated_at) if requisition.updated_at else None
    )

# Purchase Orders endpoints
@app.get("/api/purchase-orders", response_model=List[PurchaseOrderResponse], tags=["Purchase Orders"])
def get_purchase_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    vendor: Optional[str] = Query(None, description="Filter by vendor name"),
    db: Session = Depends(get_db)
):
    """Get all purchase orders with optional filtering"""
    query = db.query(PurchaseOrder)
    
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if vendor:
        query = query.filter(PurchaseOrder.vendor_name.ilike(f"%{vendor}%"))
    
    purchase_orders = query.order_by(PurchaseOrder.created_at.desc()).all()
    
    return [
        PurchaseOrderResponse(
            id=po.id,
            po_number=po.po_number,
            requisition_id=po.requisition_id,
            vendor_name=po.vendor_name,
            vendor_contact=po.vendor_contact,
            total_amount=po.total_amount,
            status=po.status,
            description=po.description,
            delivery_address=po.delivery_address,
            created_by=po.created_by,
            approved_by=po.approved_by,
            sent_date=format_central_time(po.sent_date) if po.sent_date else None,
            received_date=format_central_time(po.received_date) if po.received_date else None,
            created_at=format_central_time(po.created_at),
            updated_at=format_central_time(po.updated_at) if po.updated_at else None
        )
        for po in purchase_orders
    ]

@app.post("/api/purchase-orders", response_model=PurchaseOrderResponse, tags=["Purchase Orders"])
def create_purchase_order(purchase_order: PurchaseOrderCreate, db: Session = Depends(get_db)):
    """Create a new purchase order"""
    # Check if PO number already exists
    existing_po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == purchase_order.po_number).first()
    if existing_po:
        raise HTTPException(status_code=400, detail="Purchase order number already exists")
    
    db_purchase_order = PurchaseOrder(
        po_number=purchase_order.po_number,
        requisition_id=purchase_order.requisition_id,
        vendor_name=purchase_order.vendor_name,
        vendor_contact=purchase_order.vendor_contact,
        total_amount=purchase_order.total_amount,
        description=purchase_order.description,
        delivery_address=purchase_order.delivery_address,
        created_by=purchase_order.created_by
    )
    
    db.add(db_purchase_order)
    db.commit()
    db.refresh(db_purchase_order)
    
    return PurchaseOrderResponse(
        id=db_purchase_order.id,
        po_number=db_purchase_order.po_number,
        requisition_id=db_purchase_order.requisition_id,
        vendor_name=db_purchase_order.vendor_name,
        vendor_contact=db_purchase_order.vendor_contact,
        total_amount=db_purchase_order.total_amount,
        status=db_purchase_order.status,
        description=db_purchase_order.description,
        delivery_address=db_purchase_order.delivery_address,
        created_by=db_purchase_order.created_by,
        approved_by=db_purchase_order.approved_by,
        sent_date=format_central_time(db_purchase_order.sent_date) if db_purchase_order.sent_date else None,
        received_date=format_central_time(db_purchase_order.received_date) if db_purchase_order.received_date else None,
        created_at=format_central_time(db_purchase_order.created_at),
        updated_at=format_central_time(db_purchase_order.updated_at) if db_purchase_order.updated_at else None
    )

@app.get("/api/purchase-orders/{po_id}", response_model=PurchaseOrderResponse, tags=["Purchase Orders"])
def get_purchase_order(po_id: int, db: Session = Depends(get_db)):
    """Get a specific purchase order by ID"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    return PurchaseOrderResponse(
        id=purchase_order.id,
        po_number=purchase_order.po_number,
        requisition_id=purchase_order.requisition_id,
        vendor_name=purchase_order.vendor_name,
        vendor_contact=purchase_order.vendor_contact,
        total_amount=purchase_order.total_amount,
        status=purchase_order.status,
        description=purchase_order.description,
        delivery_address=purchase_order.delivery_address,
        created_by=purchase_order.created_by,
        approved_by=purchase_order.approved_by,
        sent_date=format_central_time(purchase_order.sent_date) if purchase_order.sent_date else None,
        received_date=format_central_time(purchase_order.received_date) if purchase_order.received_date else None,
        created_at=format_central_time(purchase_order.created_at),
        updated_at=format_central_time(purchase_order.updated_at) if purchase_order.updated_at else None
    )

@app.put("/api/purchase-orders/{po_id}/status", response_model=PurchaseOrderResponse, tags=["Purchase Orders"])
def update_purchase_order_status(po_id: int, status: str, updated_by: str, db: Session = Depends(get_db)):
    """Update purchase order status"""
    purchase_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not purchase_order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    valid_statuses = ["draft", "sent", "received", "completed", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    purchase_order.status = status
    purchase_order.updated_at = central_now()
    
    # Set specific timestamps based on status
    if status == "sent" and not purchase_order.sent_date:
        purchase_order.sent_date = central_now()
    elif status == "received" and not purchase_order.received_date:
        purchase_order.received_date = central_now()
    
    db.commit()
    db.refresh(purchase_order)
    
    return PurchaseOrderResponse(
        id=purchase_order.id,
        po_number=purchase_order.po_number,
        requisition_id=purchase_order.requisition_id,
        vendor_name=purchase_order.vendor_name,
        vendor_contact=purchase_order.vendor_contact,
        total_amount=purchase_order.total_amount,
        status=purchase_order.status,
        description=purchase_order.description,
        delivery_address=purchase_order.delivery_address,
        created_by=purchase_order.created_by,
        approved_by=purchase_order.approved_by,
        sent_date=format_central_time(purchase_order.sent_date) if purchase_order.sent_date else None,
        received_date=format_central_time(purchase_order.received_date) if purchase_order.received_date else None,
        created_at=format_central_time(purchase_order.created_at),
        updated_at=format_central_time(purchase_order.updated_at) if purchase_order.updated_at else None
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
