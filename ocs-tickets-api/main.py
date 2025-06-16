from fastapi import FastAPI, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import csv
import io
import tempfile
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
from ocs_shared_models import User, Building, Room, TechTicket, MaintenanceTicket, TicketUpdate
from ocs_shared_models.timezone_utils import central_now
from database import get_db, init_database

# Initialize database on startup
init_database()

# Create counter table if it doesn't exist and initialize counters
def init_counter_table():
    """Initialize the counter table for tracking closed tickets"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # Create counter table if it doesn't exist
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS counter (
                name VARCHAR(255) PRIMARY KEY,
                value INTEGER NOT NULL DEFAULT 0
            );
        """))
        
        # Initialize counter values if they don't exist
        db.execute(text("""
            INSERT INTO counter (name, value) 
            VALUES ('closed_tech_tickets', 0)
            ON CONFLICT (name) DO NOTHING;
        """))
        
        db.execute(text("""
            INSERT INTO counter (name, value) 
            VALUES ('closed_maintenance_tickets', 0)
            ON CONFLICT (name) DO NOTHING;
        """))
        
        db.commit()
        print("✓ Counter table initialized")
        
    except Exception as e:
        print(f"Error initializing counter table: {e}")
        db.rollback()
    finally:
        db.close()

# Initialize counter table
init_counter_table()

# Auto-update function to change "new" tickets to "open" after 48 hours
def auto_update_ticket_status():
    """Automatically update tickets from 'new' to 'open' status after 48 hours"""
    try:
        # Import here to avoid circular import issues
        from database import SessionLocal
        
        db = SessionLocal()
        
        # Calculate cutoff time (48 hours ago)
        cutoff_time = central_now() - timedelta(hours=48)
        
        # Find tech tickets that are still "new" and older than 48 hours
        tech_tickets_to_update = db.query(TechTicket).filter(
            TechTicket.status == 'new',
            TechTicket.created_at <= cutoff_time
        ).all()
        
        # Find maintenance tickets that are still "new" and older than 48 hours
        maintenance_tickets_to_update = db.query(MaintenanceTicket).filter(
            MaintenanceTicket.status == 'new',
            MaintenanceTicket.created_at <= cutoff_time
        ).all()
        
        updated_count = 0
        
        # Update tech tickets
        for ticket in tech_tickets_to_update:
            # Create update history entry
            ticket_update = TicketUpdate(
                ticket_type='tech',
                ticket_id=ticket.id,
                status_from='new',
                status_to='open',
                update_message='Automatically changed to "Open" after 48 hours',
                updated_by='System'
            )
            
            ticket.status = 'open'
            ticket.updated_at = central_now()
            
            db.add(ticket_update)
            updated_count += 1
        
        # Update maintenance tickets  
        for ticket in maintenance_tickets_to_update:
            # Create update history entry
            ticket_update = TicketUpdate(
                ticket_type='maintenance',
                ticket_id=ticket.id,
                status_from='new',
                status_to='open',
                update_message='Automatically changed to "Open" after 48 hours',
                updated_by='System'
            )
            
            ticket.status = 'open'
            ticket.updated_at = central_now()
            
            db.add(ticket_update)
            updated_count += 1
        
        # Commit all changes
        db.commit()
        
        if updated_count > 0:
            print(f"Auto-updated {updated_count} tickets from 'new' to 'open' status")
            
    except Exception as e:
        print(f"Error in auto_update_ticket_status: {str(e)}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()

# Set up background scheduler for auto-updating ticket status
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=auto_update_ticket_status,
    trigger=IntervalTrigger(hours=1),  # Check every hour
    id='auto_update_tickets',
    name='Auto-update ticket status from new to open',
    replace_existing=True
)

# Start the scheduler
scheduler.start()

# Shut down the scheduler when the app exits
atexit.register(lambda: scheduler.shutdown())

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

@app.post("/test-post")
def test_post():
    return {"message": "POST request works!", "success": True}

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
            query = query.filter(TechTicket.status.in_(['new', 'open', 'assigned', 'in_progress']))
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
            path=temp_file.name,            filename=filename,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting tech tickets: {str(e)}")

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
            query = query.filter(MaintenanceTicket.status.in_(['new', 'open', 'assigned', 'in_progress']))
        elif status_filter == "closed":
            query = query.filter(MaintenanceTicket.status == 'closed')
        elif status_filter:
            query = query.filter(MaintenanceTicket.status == status_filter)
            
        tickets = query.order_by(desc(MaintenanceTicket.created_at)).all()
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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

# Clear All Tickets API - Must come before parameterized routes
@app.post("/api/tickets/tech/clear")
def clear_all_tech_tickets(db: Session = Depends(get_db)):
    """Clear all technology tickets from the database"""
    try:
        # Get count before deletion
        count = db.query(TechTicket).count()
        
        # Delete all tech tickets
        db.query(TechTicket).delete()
        
        # Reset the closed ticket counter
        db.execute(text("""
            INSERT INTO counter (name, value) VALUES ('closed_tech_tickets', 0)
            ON CONFLICT (name) DO UPDATE SET value = 0;
        """))
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully cleared {count} technology tickets",
            "cleared_count": count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing tech tickets: {str(e)}")

@app.post("/api/tickets/maintenance/clear")
def clear_all_maintenance_tickets(db: Session = Depends(get_db)):
    """Clear all maintenance tickets from the database"""
    try:
        # Get count before deletion
        count = db.query(MaintenanceTicket).count()
        
        # Delete all maintenance tickets
        db.query(MaintenanceTicket).delete()
        
        # Reset the closed ticket counter
        db.execute(text("""
            INSERT INTO counter (name, value) VALUES ('closed_maintenance_tickets', 0)
            ON CONFLICT (name) DO UPDATE SET value = 0;
        """))        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully cleared {count} maintenance tickets",
            "cleared_count": count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing maintenance tickets: {str(e)}")

# Roll Database API - Must come before parameterized routes
@app.post("/api/tickets/tech/roll-database")
def roll_tech_database(archive_name: str, db: Session = Depends(get_db)):
    """Archive current tech tickets and create a new table"""
    try:
        # Validate archive name (only allow alphanumeric and underscore)
        if not archive_name.isalnum() and not all(c.isalnum() or c == '_' for c in archive_name):
            raise HTTPException(status_code=400, detail="Invalid archive name. Only letters, numbers, and underscores are allowed.")
            
        # Check if an archive with this name already exists
        archive_table = f"tech_tickets_archive_{archive_name}"
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{archive_table}'
            );
        """)).scalar()
        
        if table_exists:
            raise HTTPException(status_code=409, detail=f"An archive with the name '{archive_name}' already exists. Please choose a unique name.")
        
        # Create archive table as a copy of current tech_tickets
        db.execute(text(f"""
            CREATE TABLE {archive_table} AS
            SELECT * FROM tech_tickets;
        """))
        
        # Get the count of archived tickets
        archive_count = db.execute(text(f"SELECT COUNT(*) FROM {archive_table}")).scalar()
        
        # Truncate the current tech_tickets table
        db.execute(text("TRUNCATE TABLE tech_tickets RESTART IDENTITY CASCADE;"))
        
        # Reset the closed ticket counter
        db.execute(text("""
            INSERT INTO counter (name, value) VALUES ('closed_tech_tickets', 0)
            ON CONFLICT (name) DO UPDATE SET value = 0;
        """))
        
        # Commit the transaction
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully archived {archive_count} tech tickets to '{archive_table}'",
            "archive_name": archive_name,
            "archive_table": archive_table,
            "ticket_count": archive_count
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error rolling tech database: {str(e)}")

@app.post("/api/tickets/maintenance/roll-database")
def roll_maintenance_database(archive_name: str, db: Session = Depends(get_db)):
    """Archive current maintenance tickets and create a new table"""
    try:
        # Validate archive name (only allow alphanumeric and underscore)
        if not archive_name.isalnum() and not all(c.isalnum() or c == '_' for c in archive_name):
            raise HTTPException(status_code=400, detail="Invalid archive name. Only letters, numbers, and underscores are allowed.")
            
        # Check if an archive with this name already exists
        archive_table = f"maintenance_tickets_archive_{archive_name}"
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{archive_table}'
            );
        """)).scalar()
        
        if table_exists:
            raise HTTPException(status_code=409, detail=f"An archive with the name '{archive_name}' already exists. Please choose a unique name.")
        
        # Create archive table as a copy of current maintenance_tickets
        db.execute(text(f"""
            CREATE TABLE {archive_table} AS
            SELECT * FROM maintenance_tickets;
        """))
        
        # Get the count of archived tickets
        archive_count = db.execute(text(f"SELECT COUNT(*) FROM {archive_table}")).scalar()
        
        # Truncate the current maintenance_tickets table
        db.execute(text("TRUNCATE TABLE maintenance_tickets RESTART IDENTITY CASCADE;"))
        
        # Reset the closed ticket counter
        db.execute(text("""
            INSERT INTO counter (name, value) VALUES ('closed_maintenance_tickets', 0)
            ON CONFLICT (name) DO UPDATE SET value = 0;
        """))
        
        # Commit the transaction
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully archived {archive_count} maintenance tickets to '{archive_table}'",
            "archive_name": archive_name,
            "archive_table": archive_table,
            "ticket_count": archive_count
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error rolling maintenance database: {str(e)}")

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

# Archive API endpoints - these must come before parameterized routes
@app.get("/api/tickets/tech/archives")
def get_tech_archives(
    delete_archive: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of available tech ticket archives, or delete one if specified"""
    try:
        # If delete_archive is specified, delete the archive
        if delete_archive:
            # Validate the archive name to prevent SQL injection
            if not delete_archive.isalnum() and not all(c.isalnum() or c == '_' for c in delete_archive):
                raise HTTPException(status_code=400, detail="Invalid archive name")
            
            # Check if the archive table exists
            table_name = f"tech_tickets_archive_{delete_archive}"
            table_exists = db.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                );
            """)).scalar()
            
            if not table_exists:
                raise HTTPException(status_code=404, detail=f"Archive '{delete_archive}' not found")
            
            # Get the count of tickets before deletion for confirmation
            ticket_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            # Drop the archive table
            db.execute(text(f"DROP TABLE {table_name}"))
            db.commit()
            
            return {
                "success": True,
                "message": f"Archive '{delete_archive}' deleted successfully",
                "deleted_tickets": ticket_count,
                "archive_name": delete_archive
            }
        
        # Otherwise, return the list of archives
        # Query all tables that match the tech tickets archive pattern
        result = db.execute(text("""
            SELECT table_name, to_char(current_timestamp, 'YYYY-MM-DD') as created_date 
            FROM information_schema.tables 
            WHERE table_name LIKE 'tech_tickets_archive_%'
            ORDER BY table_name;
        """)).fetchall()
        
        archives = []
        for row in result:
            # Extract the archive name from the table name
            table_name = row[0]
            archive_name = table_name.replace('tech_tickets_archive_', '')
            
            # Get the count of tickets in this archive
            count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            # Get the date range of tickets in this archive
            date_range = db.execute(text(f"""
                SELECT 
                    to_char(MIN(created_at), 'YYYY-MM-DD') as oldest,
                    to_char(MAX(created_at), 'YYYY-MM-DD') as newest
                FROM {table_name}
            """)).first()
            
            archives.append({
                "name": archive_name,
                "table_name": table_name,
                "ticket_count": count,
                "created_date": row[1],
                "date_range": {
                    "oldest": date_range[0] if date_range and date_range[0] else None,
                    "newest": date_range[1] if date_range and date_range[1] else None
                }
            })
        
        return {
            "archives": archives,
            "count": len(archives)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tech archives: {str(e)}")

@app.get("/api/tickets/tech/archives/delete/{archive_name}")
def delete_tech_archive_ordered(
    archive_name: str,
    db: Session = Depends(get_db)
):
    """Delete a tech ticket archive table - placed before {archive_name} route"""
    try:
        # Validate the archive name to prevent SQL injection
        if not archive_name.isalnum() and not all(c.isalnum() or c == '_' for c in archive_name):
            raise HTTPException(status_code=400, detail="Invalid archive name")
        
        # Check if the archive table exists
        table_name = f"tech_tickets_archive_{archive_name}"
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            );
        """)).scalar()
        
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"Archive '{archive_name}' not found")
        
        # Get the count of tickets before deletion for confirmation
        ticket_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        
        # Drop the archive table
        db.execute(text(f"DROP TABLE {table_name}"))
        db.commit()
        
        return {
            "success": True,
            "message": f"Archive '{archive_name}' deleted successfully",
            "deleted_tickets": ticket_count,
            "archive_name": archive_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting tech archive: {str(e)}")

@app.get("/api/tickets/tech/archives/{archive_name}")
def get_tech_archive_tickets(
    archive_name: str,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get tickets from a specific tech ticket archive"""
    try:
        # Validate the archive name to prevent SQL injection
        if not archive_name.isalnum() and not all(c.isalnum() or c == '_' for c in archive_name):
            raise HTTPException(status_code=400, detail="Invalid archive name")
        
        # Check if the archive table exists
        table_name = f"tech_tickets_archive_{archive_name}"
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            );
        """)).scalar()
        
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"Archive '{archive_name}' not found")
        
        # Build the query based on filters
        query = f"SELECT * FROM {table_name}"
        if status_filter:
            query += f" WHERE status = '{status_filter}'"
        query += " ORDER BY id DESC"
        
        # Execute the query
        result = db.execute(text(query))
        
        # Get column names
        column_names = result.keys()
        
        # Convert to list of dicts
        tickets = []
        for row in result:
            ticket = {}
            for i, col_name in enumerate(column_names):
                if col_name in ('created_at', 'updated_at') and row[i]:
                    # Convert datetime objects to ISO format strings
                    ticket[col_name] = row[i].isoformat()
                else:                    ticket[col_name] = row[i]
            tickets.append(ticket)
            
        return {
            "archive_name": archive_name,
            "table_name": table_name,
            "tickets": tickets,
            "count": len(tickets)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tech archive tickets: {str(e)}")

# Maintenance Archives API Endpoints

@app.get("/api/tickets/maintenance/archives")
def get_maintenance_archives(
    delete_archive: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of available maintenance ticket archives, or delete one if specified"""
    try:
        # If delete_archive is specified, delete the archive
        if delete_archive:
            # Validate the archive name to prevent SQL injection
            if not delete_archive.isalnum() and not all(c.isalnum() or c == '_' for c in delete_archive):
                raise HTTPException(status_code=400, detail="Invalid archive name")
            
            # Check if the archive table exists
            table_name = f"maintenance_tickets_archive_{delete_archive}"
            table_exists = db.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                );
            """)).scalar()
            
            if not table_exists:
                raise HTTPException(status_code=404, detail=f"Archive '{delete_archive}' not found")
            
            # Get the count of tickets before deletion for confirmation
            ticket_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            # Drop the archive table
            db.execute(text(f"DROP TABLE {table_name}"))
            db.commit()
            
            return {
                "success": True,
                "message": f"Archive '{delete_archive}' deleted successfully",
                "deleted_tickets": ticket_count,
                "archive_name": delete_archive
            }
        
        # Otherwise, return the list of archives
        # Query all tables that match the maintenance tickets archive pattern
        result = db.execute(text("""
            SELECT table_name, to_char(current_timestamp, 'YYYY-MM-DD') as created_date 
            FROM information_schema.tables 
            WHERE table_name LIKE 'maintenance_tickets_archive_%'
            ORDER BY table_name;
        """)).fetchall()
        
        archives = []
        for row in result:
            # Extract the archive name from the table name
            table_name = row[0]
            archive_name = table_name.replace('maintenance_tickets_archive_', '')
            
            # Get ticket count for this archive
            ticket_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            archives.append({
                "name": archive_name,
                "table_name": table_name,
                "ticket_count": ticket_count,
                "created_date": row[1]
            })
            
        return {"archives": archives}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving maintenance archives: {str(e)}")

@app.get("/api/tickets/maintenance/archives/{archive_name}")
def get_maintenance_archive_tickets(
    archive_name: str,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get tickets from a specific maintenance ticket archive"""
    try:
        # Validate the archive name to prevent SQL injection
        if not archive_name.isalnum() and not all(c.isalnum() or c == '_' for c in archive_name):
            raise HTTPException(status_code=400, detail="Invalid archive name")
        
        # Check if the archive table exists
        table_name = f"maintenance_tickets_archive_{archive_name}"
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            );
        """)).scalar()
        
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"Archive '{archive_name}' not found")
        
        # Build the query based on filters
        query = f"SELECT * FROM {table_name}"
        if status_filter:
            query += f" WHERE status = '{status_filter}'"
        query += " ORDER BY id DESC"
        
        # Execute the query
        result = db.execute(text(query))
        
        # Get column names
        column_names = result.keys()
        
        # Convert to list of dicts
        tickets = []
        for row in result:
            ticket = {}
            for i, col_name in enumerate(column_names):
                if col_name in ('created_at', 'updated_at') and row[i]:
                    # Convert datetime objects to ISO format strings
                    ticket[col_name] = row[i].isoformat()
                else:
                    ticket[col_name] = row[i]
            tickets.append(ticket)
            
        return {
            "archive_name": archive_name,
            "table_name": table_name,
            "tickets": tickets,
            "count": len(tickets)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving maintenance archive tickets: {str(e)}")

@app.post("/api/tickets/maintenance/archives/{archive_name}/delete")
def delete_maintenance_archive(
    archive_name: str,
    db: Session = Depends(get_db)
):
    """Delete a maintenance ticket archive table"""
    try:
        # Validate the archive name to prevent SQL injection
        if not archive_name.isalnum() and not all(c.isalnum() or c == '_' for c in archive_name):
            raise HTTPException(status_code=400, detail="Invalid archive name")
        
        # Check if the archive table exists
        table_name = f"maintenance_tickets_archive_{archive_name}"
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            );
        """)).scalar()
        
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"Archive '{archive_name}' not found")
        
        # Get the count of tickets before deletion for confirmation
        ticket_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        
        # Drop the archive table
        db.execute(text(f"DROP TABLE {table_name}"))
        db.commit()
        
        return {
            "success": True,
            "message": f"Archive '{archive_name}' deleted successfully",
            "deleted_tickets": ticket_count,
            "archive_name": archive_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting maintenance archive: {str(e)}")

@app.post("/api/tickets/tech/archives/{archive_name}/delete")
def delete_tech_archive(
    archive_name: str,
    db: Session = Depends(get_db)
):
    """Delete a tech ticket archive table"""
    try:
        # Validate the archive name to prevent SQL injection
        if not archive_name.isalnum() and not all(c.isalnum() or c == '_' for c in archive_name):
            raise HTTPException(status_code=400, detail="Invalid archive name")
        
        # Check if the archive table exists
        table_name = f"tech_tickets_archive_{archive_name}"
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            );
        """)).scalar()
        
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"Archive '{archive_name}' not found")
        
        # Get the count of tickets before deletion for confirmation
        ticket_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        
        # Drop the archive table
        db.execute(text(f"DROP TABLE {table_name}"))
        db.commit()
        
        return {
            "success": True,
            "message": f"Archive '{archive_name}' deleted successfully",
            "deleted_tickets": ticket_count,
            "archive_name": archive_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting tech archive: {str(e)}")

@app.get("/api/tickets/maintenance/archives/delete/{archive_name}")
def delete_maintenance_archive_ordered(
    archive_name: str,
    db: Session = Depends(get_db)
):
    """Delete a maintenance ticket archive table - placed before {archive_name} route"""
    try:
        # Validate the archive name to prevent SQL injection
        if not archive_name.isalnum() and not all(c.isalnum() or c == '_' for c in archive_name):
            raise HTTPException(status_code=400, detail="Invalid archive name")
        
        # Check if the archive table exists
        table_name = f"maintenance_tickets_archive_{archive_name}"
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            );
        """)).scalar()
        
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"Archive '{archive_name}' not found")
        
        # Get the count of tickets before deletion for confirmation
        ticket_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        
        # Drop the archive table
        db.execute(text(f"DROP TABLE {table_name}"))
        db.commit()
        
        return {
            "success": True,
            "message": f"Archive '{archive_name}' deleted successfully",
            "deleted_tickets": ticket_count,
            "archive_name": archive_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting maintenance archive: {str(e)}")

@app.get("/api/tickets/tech/archives/delete/{archive_name}")
def delete_tech_archive_direct(
    archive_name: str,
    db: Session = Depends(get_db)
):
    """Delete a tech ticket archive table directly"""
    try:
        # Validate the archive name to prevent SQL injection
        if not archive_name.isalnum() and not all(c.isalnum() or c == '_' for c in archive_name):
            raise HTTPException(status_code=400, detail="Invalid archive name")
        
        # Check if the archive table exists
        table_name = f"tech_tickets_archive_{archive_name}"
        table_exists = db.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            );
        """)).scalar()
        
        if not table_exists:
            raise HTTPException(status_code=404, detail=f"Archive '{archive_name}' not found")
        
        # Get the count of tickets before deletion for confirmation
        ticket_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        
        # Drop the archive table
        db.execute(text(f"DROP TABLE {table_name}"))
        db.commit()
        
        return {
            "success": True,
            "message": f"Archive '{archive_name}' deleted successfully",
            "deleted_tickets": ticket_count,
            "archive_name": archive_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting tech archive: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)