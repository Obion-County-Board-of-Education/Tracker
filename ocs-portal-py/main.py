from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from ocs_shared_models import User, Building, Room, SystemMessage
from database import get_db, init_database
from services import tickets_service

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Portal (Python)")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Import and setup user/building routes from separate module
try:
    from user_building_routes import setup_user_building_routes
    setup_user_building_routes(app)
    print("✅ User and building routes imported successfully")
except Exception as e:
    print(f"❌ Error importing user/building routes: {e}")

# Homepage route
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

# Technology Ticket Routes - now use service layer
@app.get("/tickets/tech/new")
async def new_tech_ticket(request: Request):
    """Display new technology ticket form"""
    try:
        buildings = await tickets_service.get_buildings()
    except Exception as e:
        print(f"Error fetching buildings: {e}")
        buildings = []
    
    return templates.TemplateResponse("new_tech_ticket.html", {
        "request": request, 
        "buildings": buildings
    })

@app.post("/tickets/tech/new")
async def new_tech_ticket_submit(
    request: Request,
    title: str = Form(...),
    issue_type: str = Form(...),
    building: int = Form(...),
    room: int = Form(...),
    tag: str = Form(...),
    description: str = Form(...)
):
    """Process technology ticket submission via Tickets API"""
    try:
        # Get building and room names
        buildings = await tickets_service.get_buildings()
        building_obj = next((b for b in buildings if b["id"] == building), None)
        
        rooms = await tickets_service.get_building_rooms(building)
        room_obj = next((r for r in rooms if r["id"] == room), None)
        
        ticket_data = {
            "title": title,
            "description": description,
            "issue_type": issue_type,
            "building_name": building_obj["name"] if building_obj else "Unknown",
            "room_name": room_obj["name"] if room_obj else "Unknown",
            "tag": tag,
            "created_by": "System User"  # Will be replaced with actual user when authentication is implemented
        }
        
        result = await tickets_service.create_tech_ticket(ticket_data)
        if result:
            print(f"Tech ticket created: {title}")
        else:
            print(f"Failed to create tech ticket: {title}")
            
    except Exception as e:
        print(f"Error creating tech ticket: {e}")
    
    return RedirectResponse("/tickets/success", status_code=303)

@app.get("/tickets/tech/open")
async def tech_tickets_open(request: Request):
    """Display open technology tickets"""
    try:
        tickets = await tickets_service.get_tech_tickets("open")
        buildings = await tickets_service.get_buildings()
        
        # Format dates for template display
        for ticket in tickets:
            if ticket.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(ticket["created_at"].replace('Z', '+00:00'))
                    ticket["created_at"] = created_at
                except:
                    ticket["created_at"] = None
                    
            if ticket.get("updated_at"):
                try:
                    updated_at = datetime.fromisoformat(ticket["updated_at"].replace('Z', '+00:00'))
                    ticket["updated_at"] = updated_at
                except:
                    ticket["updated_at"] = None
        
    except Exception as e:
        print(f"Error fetching tickets: {e}")
        tickets = []
        buildings = []
    
    return templates.TemplateResponse("tech_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Open Technology Tickets",
        "status_filter": "open"
    })

@app.get("/tickets/tech/closed")
async def tech_tickets_closed(request: Request):
    """Display closed technology tickets"""
    try:
        tickets = await tickets_service.get_tech_tickets("closed")
        buildings = await tickets_service.get_buildings()
        
        # Format dates for template display
        for ticket in tickets:
            if ticket.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(ticket["created_at"].replace('Z', '+00:00'))
                    ticket["created_at"] = created_at
                except:
                    ticket["created_at"] = None
                    
            if ticket.get("updated_at"):
                try:
                    updated_at = datetime.fromisoformat(ticket["updated_at"].replace('Z', '+00:00'))
                    ticket["updated_at"] = updated_at
                except:
                    ticket["updated_at"] = None
        
    except Exception as e:
        print(f"Error fetching tickets: {e}")
        tickets = []
        buildings = []
    
    return templates.TemplateResponse("tech_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Closed Technology Tickets",
        "status_filter": "closed"
    })

@app.get("/tickets/tech/{ticket_id}")
async def view_tech_ticket(request: Request, ticket_id: int):
    """View individual technology ticket details"""
    try:
        ticket = await tickets_service.get_tech_ticket(ticket_id)
        if not ticket:
            return RedirectResponse("/tickets/tech/open", status_code=303)
        
        # Format dates for display
        if ticket.get("created_at"):
            try:
                created_at = datetime.fromisoformat(ticket["created_at"].replace('Z', '+00:00'))
                ticket["created_at"] = created_at.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
                
        if ticket.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(ticket["updated_at"].replace('Z', '+00:00'))
                ticket["updated_at"] = updated_at.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
        
    except Exception as e:
        print(f"Error fetching ticket: {e}")
        return RedirectResponse("/tickets/tech/open", status_code=303)
    
    return templates.TemplateResponse("tech_ticket_detail.html", {
        "request": request,
        "ticket": ticket
    })

@app.post("/tickets/tech/{ticket_id}/update")
async def update_tech_ticket_status(ticket_id: int, status: str = Form(...)):
    """Update technology ticket status via Tickets API"""
    try:
        success = await tickets_service.update_tech_ticket_status(ticket_id, status)
        if success:
            print(f"Tech ticket {ticket_id} status updated to {status}")
        else:
            print(f"Failed to update tech ticket {ticket_id} status")
    except Exception as e:
        print(f"Error updating tech ticket status: {e}")
    
    return RedirectResponse(f"/tickets/tech/{ticket_id}", status_code=303)

# Maintenance Ticket Routes - now use service layer
@app.get("/tickets/maintenance/new")
async def new_maintenance_ticket(request: Request):
    """Display new maintenance ticket form"""
    try:
        buildings = await tickets_service.get_buildings()
    except Exception as e:
        print(f"Error fetching buildings: {e}")
        buildings = []
    
    return templates.TemplateResponse("new_maintenance_ticket.html", {
        "request": request,
        "buildings": buildings
    })

@app.post("/tickets/maintenance/new")
async def new_maintenance_ticket_submit(
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
    department: str = Form("")
):
    """Process maintenance ticket submission via Tickets API"""
    try:
        # Get building and room names
        buildings = await tickets_service.get_buildings()
        building_obj = next((b for b in buildings if b["id"] == building), None)
        
        rooms = await tickets_service.get_building_rooms(building)
        room_obj = next((r for r in rooms if r["id"] == room), None)
        
        # Combine room and specific location for better context
        location_details = room_obj["name"] if room_obj else "Unknown"
        if specific_location:
            location_details += f" - {specific_location}"
        
        ticket_data = {
            "title": title,
            "description": description,
            "issue_type": issue_type,
            "building_name": building_obj["name"] if building_obj else "Unknown",
            "room_name": location_details,
            "created_by": submitted_by
        }
        
        result = await tickets_service.create_maintenance_ticket(ticket_data)
        if result:
            print(f"Maintenance ticket created: {title} by {submitted_by}")
        else:
            print(f"Failed to create maintenance ticket: {title}")
            
    except Exception as e:
        print(f"Error creating maintenance ticket: {e}")
    
    return RedirectResponse("/tickets/success", status_code=303)

@app.get("/tickets/maintenance/open")
async def maintenance_tickets_open(request: Request):
    """Display open maintenance tickets"""
    try:
        tickets = await tickets_service.get_maintenance_tickets("open")
        buildings = await tickets_service.get_buildings()
    except Exception as e:
        print(f"Error fetching tickets: {e}")
        tickets = []
        buildings = []
    
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Open Maintenance Requests", 
        "status_filter": "open"
    })

@app.get("/tickets/maintenance/closed")
async def maintenance_tickets_closed(request: Request):
    """Display closed maintenance tickets"""
    try:
        tickets = await tickets_service.get_maintenance_tickets("closed")
        buildings = await tickets_service.get_buildings()
    except Exception as e:
        print(f"Error fetching tickets: {e}")
        tickets = []
        buildings = []
    
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Closed Maintenance Requests",
        "status_filter": "closed"
    })

@app.get("/tickets/maintenance/{ticket_id}")
async def view_maintenance_ticket(request: Request, ticket_id: int):
    """View individual maintenance ticket details"""
    try:
        ticket = await tickets_service.get_maintenance_ticket(ticket_id)
        if not ticket:
            return RedirectResponse("/tickets/maintenance/open", status_code=303)
        
        # Format dates for display
        if ticket.get("created_at"):
            try:
                created_at = datetime.fromisoformat(ticket["created_at"].replace('Z', '+00:00'))
                ticket["created_at"] = created_at.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
                
        if ticket.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(ticket["updated_at"].replace('Z', '+00:00'))
                ticket["updated_at"] = updated_at.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
        
    except Exception as e:
        print(f"Error fetching ticket: {e}")
        return RedirectResponse("/tickets/maintenance/open", status_code=303)
    
    return templates.TemplateResponse("maintenance_ticket_detail.html", {
        "request": request,
        "ticket": ticket
    })

@app.post("/tickets/maintenance/{ticket_id}/update")
async def update_maintenance_ticket_status(ticket_id: int, status: str = Form(...)):
    """Update maintenance ticket status via Tickets API"""
    try:
        success = await tickets_service.update_maintenance_ticket_status(ticket_id, status)
        if success:
            print(f"Maintenance ticket {ticket_id} status updated to {status}")
        else:
            print(f"Failed to update maintenance ticket {ticket_id} status")
    except Exception as e:
        print(f"Error updating maintenance ticket status: {e}")
    
    return RedirectResponse(f"/tickets/maintenance/{ticket_id}", status_code=303)

# Building/Room API for dynamic form population
@app.get("/api/buildings/{building_id}/rooms")
async def get_building_rooms(building_id: int):
    """API endpoint to get rooms for a specific building"""
    try:
        rooms = await tickets_service.get_building_rooms(building_id)
        return {"rooms": rooms}
    except Exception as e:
        print(f"Error fetching building rooms: {e}")
        return {"rooms": []}

# Keep other non-ticket routes (inventory, users, etc.)
@app.get("/inventory/add")
def add_inventory_form(request: Request):
    return templates.TemplateResponse("add_inventory.html", {"request": request})

@app.post("/inventory/add")
def add_inventory_submit(request: Request):
    return templates.TemplateResponse("inventory_success.html", {"request": request})

@app.get("/tickets/success")
def ticket_success(request: Request):
    return templates.TemplateResponse("ticket_success.html", {"request": request})

# Note: User and Building management routes are now handled by the user_building_routes module
# imported at the top of this file. This resolves the route registration issues that were 
# preventing these routes from being properly registered in FastAPI.
