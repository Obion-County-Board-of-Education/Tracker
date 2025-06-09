from fastapi import FastAPI, Request, Depends, Form, HTTPException, UploadFile, File
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
def export_tech_tickets_csv(import_ready: str = "false", db: Session = Depends(get_db)):
    """Export all technology tickets to CSV. Use import_ready=true for import-compatible format."""
    try:
        # Convert string parameter to boolean
        import_ready_bool = import_ready.lower() in ['true', '1', 'yes', 'on']
        
        # Get all tech tickets
        tickets = db.query(TechTicket).order_by(desc(TechTicket.created_at)).all()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        
        # Write CSV headers - conditionally include ID and timestamp fields
        writer = csv.writer(temp_file)
        
        if import_ready_bool:
            # Import-ready format: exclude id, created_at, updated_at
            writer.writerow([
                'title', 'description', 'issue_type', 'school', 'room', 'tag', 
                'status', 'created_by'
            ])
        else:
            # Full format: include all fields
            writer.writerow([
                'id', 'title', 'description', 'issue_type', 'school', 'room', 'tag', 
                'status', 'created_by', 'created_at', 'updated_at'
            ])
        
        # Write ticket data
        for ticket in tickets:
            if import_ready_bool:
                # Import-ready format: exclude id, created_at, updated_at
                writer.writerow([
                    ticket.title or '',
                    ticket.description or '',
                    ticket.issue_type or '',
                    ticket.school or '',
                    ticket.room or '',
                    ticket.tag or '',
                    ticket.status,
                    ticket.created_by or ''
                ])
            else:
                # Full format: include all fields
                writer.writerow([
                    ticket.id,
                    ticket.title or '',
                    ticket.description or '',
                    ticket.issue_type or '',
                    ticket.school or '',
                    ticket.room or '',
                    ticket.tag or '',
                    ticket.status,
                    ticket.created_by or '',
                    ticket.created_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.created_at else '',
                    ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.updated_at else ''
                ])
        
        temp_file.close()
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        if import_ready_bool:
            filename = f"tech_tickets_import_ready_{current_date}.csv"
        else:
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
def export_maintenance_tickets_csv(import_ready: str = "false", db: Session = Depends(get_db)):
    """Export all maintenance tickets to CSV. Use import_ready=true for import-compatible format."""
    try:
        # Convert string parameter to boolean
        import_ready_bool = import_ready.lower() in ['true', '1', 'yes', 'on']
        
        # Get all maintenance tickets
        tickets = db.query(MaintenanceTicket).order_by(desc(MaintenanceTicket.created_at)).all()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        
        # Write CSV headers - conditionally include ID and timestamp fields
        writer = csv.writer(temp_file)
        
        if import_ready_bool:
            # Import-ready format: exclude id, created_at, updated_at
            writer.writerow([
                'title', 'description', 'issue_type', 'school', 'room', 
                'status', 'created_by'
            ])
        else:
            # Full format: include all fields
            writer.writerow([
                'id', 'title', 'description', 'issue_type', 'school', 'room', 
                'status', 'created_by', 'created_at', 'updated_at'
            ])
        
        # Write ticket data
        for ticket in tickets:
            if import_ready_bool:
                # Import-ready format: exclude id, created_at, updated_at
                writer.writerow([
                    ticket.title or '',
                    ticket.description or '',
                    ticket.issue_type or '',
                    ticket.school or '',
                    ticket.room or '',
                    ticket.status,
                    ticket.created_by or ''
                ])
            else:
                # Full format: include all fields
                writer.writerow([
                    ticket.id,
                    ticket.title or '',
                    ticket.description or '',
                    ticket.issue_type or '',
                    ticket.school or '',
                    ticket.room or '',
                    ticket.status,
                    ticket.created_by or '',
                    ticket.created_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.created_at else '',
                    ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ticket.updated_at else ''
                ])
        
        temp_file.close()
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        if import_ready_bool:
            filename = f"maintenance_tickets_import_ready_{current_date}.csv"
        else:
            filename = f"maintenance_tickets_export_{current_date}.csv"
        
        return FileResponse(
            path=temp_file.name,
            filename=filename,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting maintenance tickets: {str(e)}")

# CSV Import API
@app.post("/api/tickets/tech/import")
async def import_tech_tickets_csv(file: UploadFile = File(...), operation: str = Form(...), db: Session = Depends(get_db)):
    """Import technology tickets from CSV"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read and decode CSV file
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
            
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Check if we have valid headers
        if not csv_reader.fieldnames:
            raise HTTPException(status_code=400, detail="Invalid CSV format - no headers found")
        
        imported_count = 0
        errors = []
        
        # If overwrite mode, clear existing tickets
        if operation == "overwrite":
            db.query(TechTicket).delete()
            db.commit()
        
        # Process each row
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Find or create building
                school_name = row.get('school', '').strip()
                if not school_name:
                    errors.append(f"Row {row_num}: Missing school name")
                    continue
                    
                building = db.query(Building).filter(Building.name == school_name).first()
                if not building:
                    building = Building(name=school_name)
                    db.add(building)
                    db.flush()
                
                # Find or create room
                room_name = row.get('room', '').strip()
                if room_name:
                    room = db.query(Room).filter(Room.name == room_name, Room.building_id == building.id).first()
                    if not room:
                        room = Room(name=room_name, building_id=building.id)
                        db.add(room)
                        db.flush()
                
                # Create tech ticket
                ticket = TechTicket(
                    title=row.get('title', '').strip() or 'Imported Ticket',
                    description=row.get('description', '').strip() or '',
                    issue_type=row.get('issue_type', '').strip() or 'general',
                    status=row.get('status', 'open').strip(),
                    school=building.name,
                    room=room_name,
                    tag=row.get('tag', '').strip() if row.get('tag', '').strip() else None,
                    created_by=row.get('created_by', 'Import').strip(),
                    created_at=central_now(),
                    updated_at=central_now()
                )
                
                db.add(ticket)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        return {
            "success": True,
            "imported_count": imported_count,
            "errors": errors,
            "operation": operation
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing tech tickets: {str(e)}")

@app.post("/api/tickets/maintenance/import")
async def import_maintenance_tickets_csv(file: UploadFile = File(...), operation: str = Form(...), db: Session = Depends(get_db)):
    """Import maintenance tickets from CSV"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read and decode CSV file
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
            
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Check if we have valid headers
        if not csv_reader.fieldnames:
            raise HTTPException(status_code=400, detail="Invalid CSV format - no headers found")
        
        imported_count = 0
        errors = []
        
        # If overwrite mode, clear existing tickets
        if operation == "overwrite":
            db.query(MaintenanceTicket).delete()
            db.commit()
        
        # Process each row
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                # Find or create building
                school_name = row.get('school', '').strip()
                if not school_name:
                    errors.append(f"Row {row_num}: Missing school name")
                    continue
                    
                building = db.query(Building).filter(Building.name == school_name).first()
                if not building:
                    building = Building(name=school_name)
                    db.add(building)
                    db.flush()
                
                # Find or create room
                room_name = row.get('room', '').strip()
                if room_name:
                    room = db.query(Room).filter(Room.name == room_name, Room.building_id == building.id).first()
                    if not room:
                        room = Room(name=room_name, building_id=building.id)
                        db.add(room)
                        db.flush()
                
                # Create maintenance ticket
                ticket = MaintenanceTicket(
                    title=row.get('title', '').strip() or 'Imported Ticket',
                    description=row.get('description', '').strip() or '',
                    issue_type=row.get('issue_type', '').strip() or 'general',
                    status=row.get('status', 'open').strip(),
                    school=building.name,
                    room=room_name,
                    created_by=row.get('created_by', 'Import').strip(),
                    created_at=central_now(),
                    updated_at=central_now()
                )
                
                db.add(ticket)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        return {
            "success": True,
            "imported_count": imported_count,
            "errors": errors,
            "operation": operation
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing maintenance tickets: {str(e)}")

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
