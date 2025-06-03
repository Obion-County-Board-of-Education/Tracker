from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from ocs_shared_models import User, Building, Room, TechTicket, MaintenanceTicket
from database import get_db, init_database

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Tickets API")

# Pydantic models for API responses
class TicketBase(BaseModel):
    id: int
    title: str
    description: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TechTicketResponse(TicketBase):
    issue_type: str
    school: str
    room: str
    tag: Optional[str] = None

class MaintenanceTicketResponse(TicketBase):
    issue_type: str
    school: str
    room: str

class TicketCreateRequest(BaseModel):
    title: str
    description: str
    issue_type: str
    building_name: str
    room_name: str
    created_by: str
    tag: Optional[str] = None

@app.get("/")
def root():
    return {"message": "OCS Tickets API is running."}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ocs-tickets-api"}

# Technology Tickets API
@app.get("/api/tickets/tech", response_model=List[TechTicketResponse])
def get_tech_tickets(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get technology tickets with optional status filtering"""
    try:
        query = db.query(TechTicket)
        
        if status_filter == "open":
            query = query.filter(TechTicket.status.in_(['new', 'assigned', 'in_progress']))
        elif status_filter == "closed":
            query = query.filter(TechTicket.status.in_(['resolved', 'closed']))
        elif status_filter:
            query = query.filter(TechTicket.status == status_filter)
            
        tickets = query.order_by(desc(TechTicket.created_at)).all()
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/tickets/tech/{ticket_id}", response_model=TechTicketResponse)
def get_tech_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get a specific technology ticket"""
    ticket = db.query(TechTicket).filter(TechTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.post("/api/tickets/tech", response_model=TechTicketResponse)
def create_tech_ticket(ticket_data: TicketCreateRequest, db: Session = Depends(get_db)):
    """Create a new technology ticket"""
    try:
        new_ticket = TechTicket(
            title=ticket_data.title,
            description=ticket_data.description,
            status='new',
            school=ticket_data.building_name,
            room=ticket_data.room_name,
            tag=ticket_data.tag,
            issue_type=ticket_data.issue_type,
            created_by=ticket_data.created_by
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        return new_ticket
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating ticket: {str(e)}")

@app.put("/api/tickets/tech/{ticket_id}/status")
def update_tech_ticket_status(
    ticket_id: int, 
    status: str = Form(...), 
    db: Session = Depends(get_db)
):
    """Update technology ticket status"""
    ticket = db.query(TechTicket).filter(TechTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    try:
        ticket.status = status
        ticket.updated_at = datetime.utcnow()
        db.commit()
        return {"message": f"Ticket {ticket_id} status updated to {status}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")

# Maintenance Tickets API
@app.get("/api/tickets/maintenance", response_model=List[MaintenanceTicketResponse])
def get_maintenance_tickets(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get maintenance tickets with optional status filtering"""
    try:
        query = db.query(MaintenanceTicket)
        
        if status_filter == "open":
            query = query.filter(MaintenanceTicket.status.in_(['new', 'assigned', 'in_progress']))
        elif status_filter == "closed":
            query = query.filter(MaintenanceTicket.status.in_(['resolved', 'closed']))
        elif status_filter:
            query = query.filter(MaintenanceTicket.status == status_filter)
            
        tickets = query.order_by(desc(MaintenanceTicket.created_at)).all()
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/tickets/maintenance/{ticket_id}", response_model=MaintenanceTicketResponse)
def get_maintenance_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Get a specific maintenance ticket"""
    ticket = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.post("/api/tickets/maintenance", response_model=MaintenanceTicketResponse)
def create_maintenance_ticket(ticket_data: TicketCreateRequest, db: Session = Depends(get_db)):
    """Create a new maintenance ticket"""
    try:
        new_ticket = MaintenanceTicket(
            title=ticket_data.title,
            description=ticket_data.description,
            status='new',
            school=ticket_data.building_name,
            room=ticket_data.room_name,
            tag=ticket_data.issue_type,  # Using tag field for issue type
            issue_type=ticket_data.issue_type,
            created_by=ticket_data.created_by
        )
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        return new_ticket
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating ticket: {str(e)}")

@app.put("/api/tickets/maintenance/{ticket_id}/status")
def update_maintenance_ticket_status(
    ticket_id: int, 
    status: str = Form(...), 
    db: Session = Depends(get_db)
):
    """Update maintenance ticket status"""
    ticket = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    try:
        ticket.status = status
        ticket.updated_at = datetime.utcnow()
        db.commit()
        return {"message": f"Ticket {ticket_id} status updated to {status}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")

# Buildings API for form population
@app.get("/api/buildings")
def get_buildings(db: Session = Depends(get_db)):
    """Get all buildings"""
    try:
        buildings = db.query(Building).order_by(Building.name).all()
        return [{"id": b.id, "name": b.name} for b in buildings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/buildings/{building_id}/rooms")
def get_building_rooms(building_id: int, db: Session = Depends(get_db)):
    """Get rooms for a specific building"""
    try:
        rooms = db.query(Room).filter(Room.building_id == building_id).order_by(Room.name).all()
        return {"rooms": [{"id": r.id, "name": r.name} for r in rooms]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
