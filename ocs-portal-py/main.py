from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from ocs_shared_models import User, Building, Room, TechTicket, MaintenanceTicket, SystemMessage
from database import get_db, init_database

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Portal (Python)")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    """Home page with editable system message"""
    try:
        # Get the homepage message from database
        homepage_message = db.query(SystemMessage).filter(
            SystemMessage.message_type == 'homepage'
        ).first()
        
        # If no message exists, create a default one
        if not homepage_message:
            default_message = "You can view your open tickets that are currently in the system. You can update these tickets and even close these tickets out if you end up resolving the issue yourself. Just go to \"Tickets->Open Tickets\" to check these."
            homepage_message = SystemMessage(
                message_type='homepage',
                content=default_message,
                created_by='System'
            )
            db.add(homepage_message)
            db.commit()
            db.refresh(homepage_message)
    
    except Exception as e:
        print(f"Database error loading homepage message: {e}")
        # Fallback message if database fails
        homepage_message = type('obj', (object,), {
            'content': 'You can view your open tickets that are currently in the system. You can update these tickets and even close these tickets out if you end up resolving the issue yourself. Just go to "Tickets->Open Tickets" to check these.',
            'updated_at': None
        })()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "homepage_message": homepage_message
    })

@app.post("/update-homepage-message")
def update_homepage_message(
    request: Request,
    message_content: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update the homepage message"""
    try:
        # Get existing homepage message
        homepage_message = db.query(SystemMessage).filter(
            SystemMessage.message_type == 'homepage'
        ).first()
        
        if homepage_message:
            homepage_message.content = message_content
            homepage_message.updated_at = datetime.utcnow()
        else:
            # Create new message if it doesn't exist
            homepage_message = SystemMessage(
                message_type='homepage',
                content=message_content,
                created_by='System Admin'
            )
            db.add(homepage_message)
        
        db.commit()
        print(f"Homepage message updated successfully")
        
    except Exception as e:
        print(f"Error updating homepage message: {e}")
        db.rollback()
    
    return RedirectResponse("/", status_code=303)

@app.get("/tickets/tech/new")
def new_tech_ticket(request: Request, db: Session = Depends(get_db)):
    """Display new technology ticket form with real building data"""
    try:
        buildings = db.query(Building).order_by(Building.name).all()
    except Exception as e:
        print(f"Database error: {e}")
        buildings = []
    
    return templates.TemplateResponse("new_tech_ticket.html", {
        "request": request, 
        "buildings": buildings
    })

@app.post("/tickets/tech/new")
def new_tech_ticket_submit(
    request: Request,
    title: str = Form(...),
    issue_type: str = Form(...),
    building: int = Form(...),
    room: int = Form(...),
    tag: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process technology ticket submission"""
    try:
        # Get building and room names for storage
        building_obj = db.query(Building).filter(Building.id == building).first()
        room_obj = db.query(Room).filter(Room.id == room).first()
        
        new_ticket = TechTicket(
            title=title,
            description=description,
            status='new',
            school=building_obj.name if building_obj else 'Unknown',
            room=room_obj.name if room_obj else 'Unknown',
            tag=tag,
            issue_type=issue_type,
            created_by='System User'  # Will be replaced with actual user when authentication is implemented
        )
        db.add(new_ticket)
        db.commit()
        
        print(f"Tech ticket created: {title}")
    except Exception as e:
        print(f"Error creating tech ticket: {e}")
        db.rollback()
    
    return RedirectResponse("/tickets/success", status_code=303)

@app.get("/tickets/maintenance/new")
def new_maintenance_ticket(request: Request, db: Session = Depends(get_db)):
    """Display new maintenance ticket form with real building data"""
    try:
        buildings = db.query(Building).order_by(Building.name).all()
    except Exception as e:
        print(f"Database error: {e}")
        buildings = []
    
    return templates.TemplateResponse("new_maintenance_ticket.html", {
        "request": request,
        "buildings": buildings
    })

@app.post("/tickets/maintenance/new")
def new_maintenance_ticket_submit(
    request: Request,
    title: str = Form(...),
    issue_type: str = Form(...),
    building: int = Form(...),
    room: int = Form(...),
    specific_location: str = Form(""),
    description: str = Form(...),
    access_info: str = Form(""),
    preferred_time: str = Form(""),
    submitted_by: str = Form(...),
    contact_email: str = Form(...),
    phone: str = Form(""),
    department: str = Form(""),
    db: Session = Depends(get_db)
):
    """Process maintenance ticket submission"""
    try:
        # Get building and room names for storage
        building_obj = db.query(Building).filter(Building.id == building).first()
        room_obj = db.query(Room).filter(Room.id == room).first()
        
        # Combine room and specific location for better context
        location_details = room_obj.name if room_obj else 'Unknown'
        if specific_location:
            location_details += f" - {specific_location}"
        
        new_ticket = MaintenanceTicket(
            title=title,
            description=description,
            status='new',
            school=building_obj.name if building_obj else 'Unknown',
            room=location_details,
            tag=issue_type,  # Using tag field for issue type only
            issue_type=issue_type,
            created_by=submitted_by
        )
        db.add(new_ticket)
        db.commit()
        
        print(f"Maintenance ticket created: {title} by {submitted_by}")
    except Exception as e:
        print(f"Error creating maintenance ticket: {e}")
        db.rollback()
    
    return RedirectResponse("/tickets/success", status_code=303)

@app.get("/api/buildings/{building_id}/rooms")
def get_building_rooms(building_id: int, db: Session = Depends(get_db)):
    """API endpoint to get rooms for a specific building"""
    try:
        rooms = db.query(Room).filter(Room.building_id == building_id).order_by(Room.name).all()
        return {"rooms": [{"id": room.id, "name": room.name} for room in rooms]}
    except Exception as e:
        print(f"Database error: {e}")
        return {"rooms": []}

@app.get("/inventory/add")
def add_inventory_form(request: Request):
    return templates.TemplateResponse("add_inventory.html", {"request": request})

@app.post("/inventory/add")
def add_inventory_submit(request: Request):
    # TODO: Process form data and save to database
    return templates.TemplateResponse("inventory_success.html", {"request": request})

@app.get("/tickets/success")
def ticket_success(request: Request):
    return templates.TemplateResponse("ticket_success.html", {"request": request})

@app.get("/tickets/tech/closed")
def tech_tickets_closed(request: Request, db: Session = Depends(get_db)):
    """Display closed technology tickets"""
    try:
        tickets = db.query(TechTicket).filter(
            TechTicket.status.in_(['resolved', 'closed'])
        ).order_by(TechTicket.created_at.desc()).all()
        buildings = db.query(Building).order_by(Building.name).all()
    except Exception as e:
        print(f"Database error: {e}")
        tickets = []
        buildings = []
    
    return templates.TemplateResponse("tech_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Closed Technology Tickets",
        "status_filter": "closed"
    })

@app.get("/tickets/tech/open")
def tech_tickets_open(request: Request, db: Session = Depends(get_db)):
    """Display open technology tickets"""
    try:
        tickets = db.query(TechTicket).filter(
            TechTicket.status.in_(['new', 'assigned', 'in_progress'])
        ).order_by(TechTicket.created_at.desc()).all()
        buildings = db.query(Building).order_by(Building.name).all()
    except Exception as e:
        print(f"Database error: {e}")
        tickets = []
        buildings = []
    
    return templates.TemplateResponse("tech_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Open Technology Tickets",
        "status_filter": "open"
    })

@app.get("/tickets/maintenance/closed")
def maintenance_tickets_closed(request: Request, db: Session = Depends(get_db)):
    """Display closed maintenance tickets"""
    try:
        tickets = db.query(MaintenanceTicket).filter(
            MaintenanceTicket.status.in_(['resolved', 'closed'])
        ).order_by(MaintenanceTicket.created_at.desc()).all()
        buildings = db.query(Building).order_by(Building.name).all()
    except Exception as e:
        print(f"Database error: {e}")
        tickets = []
        buildings = []
    
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Closed Maintenance Requests",
        "status_filter": "closed"
    })

@app.get("/tickets/maintenance/open")
def maintenance_tickets_open(request: Request, db: Session = Depends(get_db)):
    """Display open maintenance tickets"""
    try:
        tickets = db.query(MaintenanceTicket).filter(
            MaintenanceTicket.status.in_(['new', 'assigned', 'in_progress'])
        ).order_by(MaintenanceTicket.created_at.desc()).all()
        buildings = db.query(Building).order_by(Building.name).all()
    except Exception as e:
        print(f"Database error: {e}")
        tickets = []
        buildings = []
    
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Open Maintenance Requests", 
        "status_filter": "open"
    })

@app.get("/tickets/tech/{ticket_id}")
def view_tech_ticket(request: Request, ticket_id: int, db: Session = Depends(get_db)):
    """View individual technology ticket details"""
    try:
        ticket = db.query(TechTicket).filter(TechTicket.id == ticket_id).first()
        if not ticket:
            # Redirect to tickets list if not found
            return RedirectResponse("/tickets/tech/all", status_code=303)
        
        ticket_data = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "issue_type": ticket.issue_type,
            "school": ticket.school,
            "room": ticket.room,
            "tag": ticket.tag,
            "created_by": ticket.created_by,
            "created_at": ticket.created_at.strftime("%B %d, %Y at %I:%M %p") if ticket.created_at else "Unknown",
            "updated_at": ticket.updated_at.strftime("%B %d, %Y at %I:%M %p") if ticket.updated_at else "Unknown"
        }
        
    except Exception as e:
        print(f"Database error: {e}")
        return RedirectResponse("/tickets/tech/all", status_code=303)
    
    return templates.TemplateResponse("tech_ticket_detail.html", {
        "request": request,
        "ticket": ticket_data
    })

@app.get("/tickets/maintenance/{ticket_id}")
def view_maintenance_ticket(request: Request, ticket_id: int, db: Session = Depends(get_db)):
    """View individual maintenance ticket details"""
    try:
        ticket = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
        if not ticket:
            # Redirect to tickets list if not found
            return RedirectResponse("/tickets/maintenance/all", status_code=303)
        
        ticket_data = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "issue_type": ticket.issue_type,
            "school": ticket.school,
            "room": ticket.room,
            "tag": ticket.tag,
            "created_by": ticket.created_by,
            "created_at": ticket.created_at.strftime("%B %d, %Y at %I:%M %p") if ticket.created_at else "Unknown",
            "updated_at": ticket.updated_at.strftime("%B %d, %Y at %I:%M %p") if ticket.updated_at else "Unknown"
        }
        
    except Exception as e:
        print(f"Database error: {e}")
        return RedirectResponse("/tickets/maintenance/all", status_code=303)
    
    return templates.TemplateResponse("maintenance_ticket_detail.html", {
        "request": request,
        "ticket": ticket_data
    })

@app.post("/tickets/tech/{ticket_id}/update")
def update_tech_ticket_status(request: Request, ticket_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    """Update technology ticket status"""
    try:
        ticket = db.query(TechTicket).filter(TechTicket.id == ticket_id).first()
        if ticket:
            ticket.status = status
            db.commit()
    except Exception as e:
        print(f"Error updating tech ticket: {e}")
        db.rollback()
    
    return RedirectResponse(f"/tickets/tech/{ticket_id}", status_code=303)

@app.post("/tickets/maintenance/{ticket_id}/update")
def update_maintenance_ticket_status(request: Request, ticket_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    """Update maintenance ticket status"""
    try:
        ticket = db.query(MaintenanceTicket).filter(MaintenanceTicket.id == ticket_id).first()
        if ticket:
            ticket.status = status
            db.commit()
    except Exception as e:
        print(f"Error updating maintenance ticket: {e}")
        db.rollback()
    
    return RedirectResponse(f"/tickets/maintenance/{ticket_id}", status_code=303)

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
                "role": user.roles.title(),
                "username": user.username,
                "building_count": building_count
            }
            users_data.append(user_info)
            
    except Exception as e:
        print(f"Database error: {e}")
        # Enhanced fallback data for demonstration
        users_data = [
            {
                "id": 1, 
                "name": "System Administrator", 
                "email": "admin@obionschools.com", 
                "role": "Admin",
                "username": "admin",
                "building_count": 5
            },
            {
                "id": 2, 
                "name": "John Smith", 
                "email": "jsmith@obionschools.com", 
                "role": "Technician",
                "username": "jsmith",
                "building_count": 2
            },
            {
                "id": 3, 
                "name": "Mary Wilson", 
                "email": "mwilson@obionschools.com", 
                "role": "User",
                "username": "mwilson",
                "building_count": 1
            },
        ]
    
    return templates.TemplateResponse("users.html", {"request": request, "users": users_data})

@app.get("/users/add")
def add_user_form(request: Request):
    return templates.TemplateResponse("add_user.html", {"request": request})

@app.post("/users/add")
def add_user_submit(request: Request, name: str = Form(...), email: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    """Add new user to database"""
    try:
        # Create username from name (simple approach)
        username = name.lower().replace(" ", "")
        
        new_user = User(
            username=username,
            display_name=name,
            email=email,
            roles=role.lower()
        )
        db.add(new_user)
        db.commit()
    except Exception as e:
        print(f"Error adding user: {e}")
        db.rollback()
    
    return RedirectResponse("/users/list", status_code=303)

@app.get("/users/edit/{user_id}")
def edit_user_form(request: Request, user_id: int, db: Session = Depends(get_db)):
    """Edit user form with data from database"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user_data = {
                "id": user.id,
                "name": user.display_name or user.username,
                "email": user.email or f"{user.username}@obionschools.com",
                "role": user.roles.title()
            }
        else:
            user_data = {"id": user_id, "name": "User Not Found", "email": "", "role": "User"}
    except Exception as e:
        print(f"Database error: {e}")
        user_data = {"id": user_id, "name": "Sample User", "email": "sample@example.com", "role": "User"}
    
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user_data})

@app.post("/users/edit/{user_id}")
def edit_user_submit(request: Request, user_id: int, name: str = Form(...), email: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    """Update user in database"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.display_name = name
            user.email = email
            user.roles = role.lower()
            db.commit()
    except Exception as e:
        print(f"Error updating user: {e}")
        db.rollback()
    
    return RedirectResponse("/users/list", status_code=303)

@app.post("/users/delete/{user_id}")
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    """Delete user from database"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
    except Exception as e:
        print(f"Error deleting user: {e}")
        db.rollback()
    
    return RedirectResponse("/users/list", status_code=303)

@app.get("/users/view/{user_id}")
def view_user_detail(request: Request, user_id: int, db: Session = Depends(get_db)):
    """View detailed information about a specific user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Get user's building and room assignments
            buildings = user.buildings if user.buildings else []
            rooms = user.rooms if user.rooms else []
            
            user_data = {
                "id": user.id,
                "name": user.display_name or user.username,
                "username": user.username,
                "email": user.email or f"{user.username}@obionschools.com",
                "role": user.roles.title(),
                "buildings": [{"id": b.id, "name": b.name} for b in buildings],
                "rooms": [{"id": r.id, "name": r.name, "building_name": r.building.name if r.building else "Unknown"} for r in rooms],
                "building_count": len(buildings),
                "room_count": len(rooms)
            }
        else:
            user_data = None
    except Exception as e:
        print(f"Database error: {e}")
        user_data = {
            "id": user_id,
            "name": "Sample User",
            "username": "sampleuser",
            "email": "sample@obionschools.com",
            "role": "User",
            "buildings": [{"id": 1, "name": "Sample Building"}],
            "rooms": [{"id": 1, "name": "Room 101", "building_name": "Sample Building"}],
            "building_count": 1,
            "room_count": 1
        }
    
    return templates.TemplateResponse("user_detail.html", {"request": request, "user": user_data})

@app.get("/users/roles")
def manage_roles(request: Request):
    """Display detailed role permissions and access levels"""
    roles = [
        {
            "id": 1, 
            "name": "Admin", 
            "permissions": [
                "manage_users", 
                "manage_tickets", 
                "manage_inventory", 
                "manage_buildings", 
                "manage_requisitions",
                "system_settings",
                "view_reports",
                "delete_records"
            ]
        },
        {
            "id": 2, 
            "name": "Technician", 
            "permissions": [
                "view_tickets", 
                "update_tickets", 
                "manage_inventory", 
                "view_buildings",
                "create_tech_tickets",
                "close_tickets"
            ]
        },
        {
            "id": 3, 
            "name": "User", 
            "permissions": [
                "submit_ticket", 
                "view_own_tickets", 
                "update_profile",
                "create_requisitions",
                "view_buildings"
            ]
        },
    ]
    return templates.TemplateResponse("manage_roles.html", {"request": request, "roles": roles})

# Buildings Management Routes
@app.get("/buildings/list")
def buildings_list(request: Request, db: Session = Depends(get_db)):
    """List all buildings with their room counts, sorted alphabetically by name"""
    try:
        # Sort buildings alphabetically by name
        buildings = db.query(Building).order_by(Building.name).all()
        buildings_data = []
        for building in buildings:
            room_count = db.query(Room).filter(Room.building_id == building.id).count()
            buildings_data.append({
                "id": building.id,
                "name": building.name,
                "room_count": room_count,
                "created_at": building.created_at.strftime("%Y-%m-%d") if building.created_at else "N/A"
            })
    except Exception as e:
        print(f"Database error: {e}")
        buildings_data = []
    
    return templates.TemplateResponse("buildings.html", {"request": request, "buildings": buildings_data})

@app.get("/buildings/add")
def add_building_form(request: Request):
    return templates.TemplateResponse("add_building.html", {"request": request})

@app.post("/buildings/add")
def add_building_submit(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    """Add new building to database"""
    try:
        new_building = Building(name=name)
        db.add(new_building)
        db.commit()
    except Exception as e:
        print(f"Error adding building: {e}")
        db.rollback()
    
    return RedirectResponse("/buildings/list", status_code=303)

@app.get("/buildings/edit/{building_id}")
def edit_building_form(request: Request, building_id: int, db: Session = Depends(get_db)):
    """Edit building form with data from database"""
    try:
        building = db.query(Building).filter(Building.id == building_id).first()
        if building:
            building_data = {
                "id": building.id,
                "name": building.name
            }
        else:
            building_data = {"id": building_id, "name": "Building Not Found"}
    except Exception as e:
        print(f"Database error: {e}")
        building_data = {"id": building_id, "name": "Sample Building"}
    
    return templates.TemplateResponse("edit_building.html", {"request": request, "building": building_data})

@app.post("/buildings/edit/{building_id}")
def edit_building_submit(request: Request, building_id: int, name: str = Form(...), db: Session = Depends(get_db)):
    """Update building in database"""
    try:
        building = db.query(Building).filter(Building.id == building_id).first()
        if building:
            building.name = name
            db.commit()
    except Exception as e:
        print(f"Error updating building: {e}")
        db.rollback()
    
    return RedirectResponse("/buildings/list", status_code=303)

@app.post("/buildings/delete/{building_id}")
def delete_building(request: Request, building_id: int, db: Session = Depends(get_db)):
    """Delete building and all associated rooms from database"""
    try:
        # First delete all rooms in this building
        db.query(Room).filter(Room.building_id == building_id).delete()
        # Then delete the building
        building = db.query(Building).filter(Building.id == building_id).first()
        if building:
            db.delete(building)
            db.commit()
    except Exception as e:
        print(f"Error deleting building: {e}")
        db.rollback()
    
    return RedirectResponse("/buildings/list", status_code=303)

@app.get("/buildings/{building_id}/rooms")
def building_rooms(request: Request, building_id: int, db: Session = Depends(get_db)):
    """List all rooms in a specific building"""
    try:
        building = db.query(Building).filter(Building.id == building_id).first()
        if building:
            rooms = db.query(Room).filter(Room.building_id == building_id).all()
            rooms_data = [
                {
                    "id": room.id,
                    "name": room.name
                }
                for room in rooms
            ]
            building_data = {"id": building.id, "name": building.name}
        else:
            building_data = {"id": building_id, "name": "Building Not Found"}
            rooms_data = []
    except Exception as e:
        print(f"Database error: {e}")
        building_data = {"id": building_id, "name": "Sample Building"}
        rooms_data = []
    
    return templates.TemplateResponse("building_rooms.html", {
        "request": request, 
        "building": building_data, 
        "rooms": rooms_data
    })

@app.post("/buildings/{building_id}/rooms/add")
def add_room_submit(request: Request, building_id: int, room_name: str = Form(...), db: Session = Depends(get_db)):
    """Add new room to building"""
    try:
        new_room = Room(name=room_name, building_id=building_id)
        db.add(new_room)
        db.commit()
    except Exception as e:
        print(f"Error adding room: {e}")
        db.rollback()
    
    return RedirectResponse(f"/buildings/{building_id}/rooms", status_code=303)

@app.post("/buildings/{building_id}/rooms/delete/{room_id}")
def delete_room(request: Request, building_id: int, room_id: int, db: Session = Depends(get_db)):
    """Delete room from building"""
    try:
        room = db.query(Room).filter(Room.id == room_id, Room.building_id == building_id).first()
        if room:
            db.delete(room)
            db.commit()
    except Exception as e:
        print(f"Error deleting room: {e}")
        db.rollback()
    
    return RedirectResponse(f"/buildings/{building_id}/rooms", status_code=303)
