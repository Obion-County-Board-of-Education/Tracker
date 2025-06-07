from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import csv
import io
import tempfile
import os
from ocs_shared_models import User, Building, Room, TechTicket, MaintenanceTicket, TicketUpdate
from ocs_shared_models.timezone_utils import central_now
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

class TicketUpdateRequest(BaseModel):
    status: str
    update_message: str
    updated_by: str

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
            query = query.filter(TechTicket.status == 'closed')
        elif status_filter:
            query = query.filter(TechTicket.status == status_filter)
            
        tickets = query.order_by(desc(TechTicket.created_at)).all()
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# CSV Export API - Must come before parameterized routes
@app.get("/api/tickets/tech/export")
def export_tech_tickets_csv(db: Session = Depends(get_db)):
    """Export all technology tickets to CSV"""
    try:
        # Get all tech tickets
        tickets = db.query(TechTicket).order_by(desc(TechTicket.created_at)).all()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        
        # Write CSV headers
        writer = csv.writer(temp_file)
        writer.writerow([
            'ID', 'Title', 'Description', 'Issue Type', 'School', 'Room', 'Tag', 
            'Status', 'Created By', 'Created At', 'Updated At'
        ])
        
        # Write ticket data
        for ticket in tickets:
            writer.writerow([
                ticket.id,
                ticket.title,
                ticket.description,
                ticket.issue_type or '',
                ticket.school or '',
                ticket.room or '',
                ticket.tag or '',
                ticket.status,
                ticket.created_by,
                ticket.created_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.created_at else '',
                ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.updated_at else ''
            ])
        
        temp_file.close()
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f"tech_tickets_export_{current_date}.csv"
        
        return FileResponse(
            path=temp_file.name,
            filename=filename,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting tech tickets: {str(e)}")

@app.get("/api/tickets/maintenance/export")
def export_maintenance_tickets_csv(db: Session = Depends(get_db)):
    """Export all maintenance tickets to CSV"""
    try:
        # Get all maintenance tickets
        tickets = db.query(MaintenanceTicket).order_by(desc(MaintenanceTicket.created_at)).all()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        
        # Write CSV headers
        writer = csv.writer(temp_file)
        writer.writerow([
            'ID', 'Title', 'Description', 'Issue Type', 'School', 'Room', 
            'Status', 'Created By', 'Created At', 'Updated At'
        ])
        
        # Write ticket data
        for ticket in tickets:
            writer.writerow([
                ticket.id,
                ticket.title,
                ticket.description,
                ticket.issue_type or '',
                ticket.school or '',
                ticket.room or '',
                ticket.status,
                ticket.created_by,
                ticket.created_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.created_at else '',
                ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.updated_at else ''
            ])
        
        temp_file.close()
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f"maintenance_tickets_export_{current_date}.csv"
        
        return FileResponse(
            path=temp_file.name,
            filename=filename,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting maintenance tickets: {str(e)}")

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
        ticket.updated_at = central_now()
        db.commit()
        return {"message": f"Ticket {ticket_id} status updated to {status}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")

@app.put("/api/tickets/tech/{ticket_id}")
def update_tech_ticket(
    ticket_id: int, 
    update_data: TicketUpdateRequest, 
    db: Session = Depends(get_db)
):
    """Update technology ticket with status and message"""
    ticket = db.query(TechTicket).filter(TechTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    try:
        # Store previous status for update history
        previous_status = ticket.status
        
        # Update ticket status
        ticket.status = update_data.status
        ticket.updated_at = central_now()
        
        # Create update history entry
        ticket_update = TicketUpdate(
            ticket_type='tech',
            ticket_id=ticket_id,
            status_from=previous_status,
            status_to=update_data.status,
            update_message=update_data.update_message,
            updated_by=update_data.updated_by
        )
        
        db.add(ticket_update)
        db.commit()
        return {"message": f"Ticket {ticket_id} updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")

# Ticket Updates API
@app.get("/api/tickets/{ticket_type}/{ticket_id}/updates")
def get_ticket_updates(ticket_type: str, ticket_id: int, db: Session = Depends(get_db)):
    """Get update history for a ticket"""
    try:
        updates = db.query(TicketUpdate).filter(
            TicketUpdate.ticket_type == ticket_type,
            TicketUpdate.ticket_id == ticket_id
        ).order_by(TicketUpdate.created_at.desc()).all()
        
        return [{
            "id": update.id,
            "status_from": update.status_from,
            "status_to": update.status_to,
            "update_message": update.update_message,
            "updated_by": update.updated_by,
            "created_at": update.created_at.isoformat()
        } for update in updates]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching updates: {str(e)}")

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
            query = query.filter(MaintenanceTicket.status == 'closed')
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
        ticket.updated_at = central_now()
        db.commit()
        return {"message": f"Ticket {ticket_id} status updated to {status}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")

@app.put("/api/tickets/maintenance/{ticket_id}")
def update_maintenance_ticket(
    ticket_id: int, 
    update_data: TicketUpdateRequest, 
    db: Session = Depends(get_db)
):
    """Update maintenance ticket with status and message"""
    ticket = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    try:
        # Store previous status for update history
        previous_status = ticket.status
        
        # Update ticket status
        ticket.status = update_data.status
        ticket.updated_at = central_now()
        
        # Create update history entry
        ticket_update = TicketUpdate(
            ticket_type='maintenance',
            ticket_id=ticket_id,
            status_from=previous_status,
            status_to=update_data.status,
            update_message=update_data.update_message,
            updated_by=update_data.updated_by
        )
        
        db.add(ticket_update)
        db.commit()
        return {"message": f"Ticket {ticket_id} updated successfully"}
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

# Clear/Delete All Tickets API
@app.delete("/api/tickets/tech/clear")
def clear_all_tech_tickets(db: Session = Depends(get_db)):
    """Clear all technology tickets from the database"""
    try:
        # Delete all ticket updates for tech tickets first (foreign key constraint)
        db.execute(text("DELETE FROM ticket_updates WHERE ticket_type = 'tech'"))
        
        # Delete all tech tickets
        deleted_count = db.query(TechTicket).delete()
        
        db.commit()
        return {"message": f"Successfully cleared {deleted_count} technology tickets"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing tech tickets: {str(e)}")

@app.delete("/api/tickets/maintenance/clear")
def clear_all_maintenance_tickets(db: Session = Depends(get_db)):
    """Clear all maintenance tickets from the database"""
    try:
        # Delete all ticket updates for maintenance tickets first (foreign key constraint)
        db.execute(text("DELETE FROM ticket_updates WHERE ticket_type = 'maintenance'"))
        
        # Delete all maintenance tickets
        deleted_count = db.query(MaintenanceTicket).delete()
        
        db.commit()
        return {"message": f"Successfully cleared {deleted_count} maintenance tickets"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing maintenance tickets: {str(e)}")
