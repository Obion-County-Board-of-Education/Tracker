import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from ocs_shared_models import User, Building, Room, SystemMessage
from ocs_shared_models.timezone_utils import central_now, format_central_time
from database import get_db, init_database
from services import tickets_service, purchasing_service
from management_service import management_service
from service_health import health_checker

# Initialize database on startup
try:
    init_database()
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")
    print("🔄 Starting application without database connection")

app = FastAPI(title="OCS Portal (Python)")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

async def get_menu_context():
    """Get menu visibility context for templates"""
    try:
        menu_visibility = await health_checker.get_menu_visibility()
        print(f"🔍 Dynamic menu context: {menu_visibility}")
        return {"menu_visibility": menu_visibility}
    except Exception as e:
        print(f"⚠️ Health checker failed, using fallback menu: {e}")        # Fallback to show all menus if health checker fails
        return {"menu_visibility": {
            "tickets": True,
            "inventory": True,
            "purchasing": True,
            "manage": True,
            "forms": True,
            "admin": True
        }}

async def render_template(template_name: str, context: dict):
    """Helper function to render templates with menu context"""
    menu_context = await get_menu_context()
    return templates.TemplateResponse(template_name, {**context, **menu_context})

# Import and setup user/building routes from separate module
try:
    from user_building_routes import setup_user_building_routes
    setup_user_building_routes(app, get_menu_context, render_template)
    print("✅ User and building routes imported successfully")
except Exception as e:
    print(f"❌ Error importing user/building routes: {e}")

# Homepage route
@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    """Home page with editable system message and dashboard"""
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
      # Gather dashboard data
    try:
        dashboard_data = await get_dashboard_data(db)
    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        # Provide fallback dashboard data
        dashboard_data = {
            "tickets": {"tech_open": 0, "tech_closed": 0, "maintenance_open": 0, "maintenance_closed": 0, "total_open": 0, "total_closed": 0},
            "buildings": {"total_buildings": 0, "total_rooms": 0, "buildings_with_rooms": 0},
            "users": {"total_users": 0, "admin_users": 0, "regular_users": 0},
            "recent_activity": [],
            "service_health": {}
        }
    
    # Get menu visibility context
    menu_context = await get_menu_context()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "homepage_message": homepage_message,
        "dashboard_data": dashboard_data,
        **menu_context
    })

async def get_dashboard_data(db: Session):
    """Gather data for dashboard charts"""
    try:
        dashboard = {
            "tickets": {
                "tech_open": 0,
                "tech_closed": 0,
                "maintenance_open": 0,
                "maintenance_closed": 0,
                "total_open": 0,
                "total_closed": 0
            },
            "buildings": {
                "total_buildings": 0,
                "total_rooms": 0,
                "buildings_with_rooms": 0
            },
            "users": {
                "total_users": 0,
                "admin_users": 0,
                "regular_users": 0
            },
            "recent_activity": [],
            "ticket_trends": [],
            "service_health": {}
        }
        
        # Get ticket data from APIs
        try:
            tech_open = await tickets_service.get_tech_tickets("open")
            tech_closed = await tickets_service.get_tech_tickets("closed")
            maintenance_open = await tickets_service.get_maintenance_tickets("open")
            maintenance_closed = await tickets_service.get_maintenance_tickets("closed")
            
            dashboard["tickets"]["tech_open"] = len(tech_open) if tech_open else 0
            dashboard["tickets"]["tech_closed"] = len(tech_closed) if tech_closed else 0
            dashboard["tickets"]["maintenance_open"] = len(maintenance_open) if maintenance_open else 0
            dashboard["tickets"]["maintenance_closed"] = len(maintenance_closed) if maintenance_closed else 0
            dashboard["tickets"]["total_open"] = dashboard["tickets"]["tech_open"] + dashboard["tickets"]["maintenance_open"]
            dashboard["tickets"]["total_closed"] = dashboard["tickets"]["tech_closed"] + dashboard["tickets"]["maintenance_closed"]
            
            # Get recent activity from recent tickets
            recent_tickets = []
            if tech_open:
                recent_tickets.extend(tech_open[:5])
            if maintenance_open:
                recent_tickets.extend(maintenance_open[:5])
            
            # Sort by creation date and take most recent
            if recent_tickets:
                sorted_tickets = sorted(recent_tickets, 
                                      key=lambda x: x.get('created_at', ''), 
                                      reverse=True)[:5]
                dashboard["recent_activity"] = [
                    {
                        "type": "ticket",
                        "title": ticket.get('title', 'Unknown'),
                        "category": "Tech" if "tech" in str(ticket.get('id', '')).lower() else "Maintenance",
                        "created_at": ticket.get('created_at', 'Unknown'),
                        "status": ticket.get('status', 'open')
                    }
                    for ticket in sorted_tickets
                ]
                
        except Exception as e:
            print(f"Error fetching ticket data for dashboard: {e}")
        
        # Get building and room data from database
        try:
            buildings = db.query(Building).all()
            rooms = db.query(Room).all()
            
            dashboard["buildings"]["total_buildings"] = len(buildings)
            dashboard["buildings"]["total_rooms"] = len(rooms)
            dashboard["buildings"]["buildings_with_rooms"] = len([b for b in buildings if b.rooms])
            
        except Exception as e:
            print(f"Error fetching building data for dashboard: {e}")
        
        # Get user data from database
        try:
            users = db.query(User).all()
            dashboard["users"]["total_users"] = len(users)
            dashboard["users"]["admin_users"] = len([u for u in users if u.roles and 'admin' in u.roles.lower()])
            dashboard["users"]["regular_users"] = dashboard["users"]["total_users"] - dashboard["users"]["admin_users"]
            
        except Exception as e:
            print(f"Error fetching user data for dashboard: {e}")
        
        # Get service health
        try:
            dashboard["service_health"] = await health_checker.get_service_health()
        except Exception as e:
            print(f"Error fetching service health for dashboard: {e}")
            dashboard["service_health"] = {}
        
        return dashboard
        
    except Exception as e:
        print(f"Error gathering dashboard data: {e}")
        return {
            "tickets": {"tech_open": 0, "tech_closed": 0, "maintenance_open": 0, "maintenance_closed": 0, "total_open": 0, "total_closed": 0},
            "buildings": {"total_buildings": 0, "total_rooms": 0, "buildings_with_rooms": 0},
            "users": {"total_users": 0, "admin_users": 0, "regular_users": 0},
            "recent_activity": [],
            "service_health": {}
        }

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
            SystemMessage.message_type == 'homepage'        ).first()
        
        if homepage_message:
            homepage_message.content = message_content
            homepage_message.updated_at = central_now()
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
    # Get menu context
    menu_context = await get_menu_context()
    
    return templates.TemplateResponse("new_tech_ticket.html", {
        "request": request, 
        "buildings": buildings,
        **menu_context
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
        closed_count = await tickets_service.get_closed_tickets_count("tech")
        
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
        closed_count = 0
    
    # Get menu context
    menu_context = await get_menu_context()
    
    return templates.TemplateResponse("tech_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "closed_count": closed_count,
        "page_title": "Open Technology Tickets",
        "status_filter": "open",
        "current_datetime": datetime.now(),
        **menu_context
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
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("tech_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Closed Technology Tickets",
        "status_filter": "closed",
        "current_datetime": datetime.now(),
        **menu_context
    })

# CSV Export Routes - Must come before parameterized routes
@app.get("/tickets/tech/export")
async def export_tech_tickets(request: Request):
    """Export tech tickets to CSV"""
    try:
        csv_content = await tickets_service.export_tech_tickets_csv()
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f"tech_tickets_export_{current_date}.csv"
        
        return Response(
            content=csv_content,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"❌ Error exporting tech tickets: {e}")
        # Return to the tickets page with error
        return RedirectResponse("/tickets/tech/open", status_code=303)

# CSV Import Routes
@app.post("/tickets/tech/import")
async def import_tech_tickets(request: Request, file: UploadFile = File(...), operation: str = Form(...)):
    """Import tech tickets from CSV"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Call the import service
        result = await tickets_service.import_tech_tickets_csv(file_content, operation)
        
        print(f"✅ Tech tickets import successful: {result}")
        
        # Parse the result to get import count
        import_count = "unknown"
        if result and "imported" in str(result).lower():
            # Try to extract the number from the result
            import re
            match = re.search(r'(\d+)', str(result))
            if match:
                import_count = match.group(1)
        
        return RedirectResponse(f"/tickets/tech/open?import_success=true&count={import_count}&mode={operation}", status_code=303)
    except Exception as e:
        print(f"❌ Error importing tech tickets: {e}")
        error_msg = str(e).replace("'", "").replace('"', "")[:100]  # Sanitize and limit length
        return RedirectResponse(f"/tickets/tech/open?import_error=true&message={error_msg}", status_code=303)

@app.get("/tickets/tech/{ticket_id}")
async def view_tech_ticket(request: Request, ticket_id: int):
    """View individual technology ticket details"""
    try:
        ticket = await tickets_service.get_tech_ticket(ticket_id)
        if not ticket:
            return RedirectResponse("/tickets/tech/open", status_code=303)
        
        # Get ticket update history
        updates = await tickets_service.get_ticket_updates("tech", ticket_id)
        
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
        
        # Format update timestamps
        for update in updates:
            try:
                created_at = datetime.fromisoformat(update["created_at"].replace('Z', '+00:00'))
                update["created_at"] = created_at.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
        
    except Exception as e:
        print(f"Error fetching ticket: {e}")
        return RedirectResponse("/tickets/tech/open", status_code=303)
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("tech_ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        "updates": updates,
        **menu_context
    })

@app.post("/tickets/tech/{ticket_id}/update")
async def update_tech_ticket_status(
    ticket_id: int,
    status: str = Form(...),
    update_message: str = Form(default="")
):
    """Update technology ticket status and add update message via Tickets API"""
    try:
        if update_message.strip():
            update_data = {
                "status": status,
                "update_message": update_message.strip(),
                "updated_by": "System User"  # Replace with actual user when auth is implemented
            }
            success = await tickets_service.update_tech_ticket_comprehensive(ticket_id, update_data)
        else:
            success = await tickets_service.update_tech_ticket_status(ticket_id, status)
        if success:
            print(f"Tech ticket {ticket_id} updated - Status: {status}")
        else:
            print(f"Failed to update tech ticket {ticket_id}")
    except Exception as e:
        print(f"Error updating tech ticket: {e}")
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
    
    # Get menu context
    menu_context = await get_menu_context()
    
    return templates.TemplateResponse("new_maintenance_ticket.html", {
        "request": request,
        "buildings": buildings,
        **menu_context
    })

@app.post("/tickets/maintenance/new")
async def new_maintenance_ticket_submit(
    request: Request,
    title: str = Form(...),
    issue_type: str = Form(...),
    building: int = Form(...),
    room: int = Form(...),
    description: str = Form(...)
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
        
        ticket_data = {
            "title": title,
            "description": description,            "issue_type": issue_type,
            "building_name": building_obj["name"] if building_obj else "Unknown",
            "room_name": location_details,
            "created_by": "System User"  # Default user until authentication is implemented
        }
        
        result = await tickets_service.create_maintenance_ticket(ticket_data)
        if result:
            print(f"Maintenance ticket created: {title}")
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
        closed_count = await tickets_service.get_closed_tickets_count("maintenance")
        
        # Format dates for template display
        for ticket in tickets:
            if ticket.get("created_at"):
                try:
                    # Handle various datetime formats
                    date_str = ticket["created_at"]
                    # Add seconds if missing (e.g., "2025-06-06T21:08" -> "2025-06-06T21:08:00")
                    if len(date_str) == 16 and 'T' in date_str:
                        date_str += ":00"
                    # Remove Z timezone and add UTC offset
                    date_str = date_str.replace('Z', '+00:00')
                    created_at = datetime.fromisoformat(date_str)
                    ticket["created_at"] = created_at
                except Exception as e:
                    print(f"Warning: Could not parse created_at '{ticket.get('created_at')}': {e}")
                    # If parsing fails, create a default datetime
                    ticket["created_at"] = datetime.now()
            else:
                # If no created_at, set to current time
                ticket["created_at"] = datetime.now()
                    
            if ticket.get("updated_at"):
                try:
                    # Handle various datetime formats
                    date_str = ticket["updated_at"]
                    # Add seconds if missing
                    if len(date_str) == 16 and 'T' in date_str:
                        date_str += ":00"                    # Remove Z timezone and add UTC offset
                    date_str = date_str.replace('Z', '+00:00')
                    updated_at = datetime.fromisoformat(date_str)
                    ticket["updated_at"] = updated_at
                except Exception as e:
                    print(f"Warning: Could not parse updated_at '{ticket.get('updated_at')}': {e}")
                    ticket["updated_at"] = None
            else:
                ticket["updated_at"] = None
                    
    except Exception as e:
        print(f"Error fetching tickets: {e}")
        tickets = []
        buildings = []
        closed_count = 0
        
    # Get menu context
    menu_context = await get_menu_context()
    
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "closed_count": closed_count,
        "page_title": "Open Maintenance Requests", 
        "status_filter": "open",
        "current_datetime": datetime.now(),
        **menu_context
    })

@app.get("/tickets/maintenance/closed")
async def maintenance_tickets_closed(request: Request):
    """Display closed maintenance tickets"""
    try:
        tickets = await tickets_service.get_maintenance_tickets("closed")
        buildings = await tickets_service.get_buildings()
        
        # Format dates for template display
        for ticket in tickets:
            if ticket.get("created_at"):
                try:
                    # Handle various datetime formats
                    date_str = ticket["created_at"]
                    # Add seconds if missing (e.g., "2025-06-06T21:08" -> "2025-06-06T21:08:00")
                    if len(date_str) == 16 and 'T' in date_str:
                        date_str += ":00"
                    # Remove Z timezone and add UTC offset
                    date_str = date_str.replace('Z', '+00:00')
                    created_at = datetime.fromisoformat(date_str)
                    ticket["created_at"] = created_at
                except Exception as e:
                    print(f"Warning: Could not parse created_at '{ticket.get('created_at')}': {e}")
                    ticket["created_at"] = None
                    
            if ticket.get("updated_at"):
                try:
                    # Handle various datetime formats
                    date_str = ticket["updated_at"]
                    # Add seconds if missing
                    if len(date_str) == 16 and 'T' in date_str:
                        date_str += ":00"                    # Remove Z timezone and add UTC offset
                    date_str = date_str.replace('Z', '+00:00')
                    updated_at = datetime.fromisoformat(date_str)
                    ticket["updated_at"] = updated_at
                except Exception as e:
                    print(f"Warning: Could not parse updated_at '{ticket.get('updated_at')}': {e}")
                    ticket["updated_at"] = None
            else:
                ticket["updated_at"] = None
        
    except Exception as e:
        print(f"Error fetching tickets: {e}")
        tickets = []
        buildings = []
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Closed Maintenance Requests",        "status_filter": "closed",
        "current_datetime": datetime.now(),
        **menu_context
    })

@app.get("/tickets/tech/archive")
async def tech_tickets_archive(request: Request):
    """Display archived technology tickets"""
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

    menu_context = await get_menu_context()
    return templates.TemplateResponse("tech_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Archived Technology Tickets",
        "status_filter": "archived",
        "current_datetime": datetime.now(),
        **menu_context
    })

@app.get("/tickets/maintenance/archive")
async def maintenance_tickets_archive(request: Request):
    """Display archived maintenance tickets"""
    try:
        tickets = await tickets_service.get_maintenance_tickets("closed")
        buildings = await tickets_service.get_buildings()
        
        # Format dates for template display  
        for ticket in tickets:
            if ticket.get("created_at"):
                try:
                    date_str = ticket["created_at"]
                    if len(date_str) == 16 and 'T' in date_str:
                        date_str += ":00"
                    date_str = date_str.replace('Z', '+00:00')
                    created_at = datetime.fromisoformat(date_str)
                    ticket["created_at"] = created_at
                except Exception as e:
                    ticket["created_at"] = datetime.now()
            else:
                ticket["created_at"] = datetime.now()
                    
            if ticket.get("updated_at"):
                try:
                    date_str = ticket["updated_at"]
                    if len(date_str) == 16 and 'T' in date_str:
                        date_str += ":00"
                    date_str = date_str.replace('Z', '+00:00')
                    updated_at = datetime.fromisoformat(date_str)
                    ticket["updated_at"] = updated_at
                except Exception as e:
                    ticket["updated_at"] = None
            else:
                ticket["updated_at"] = None
        
    except Exception as e:
        print(f"Error fetching tickets: {e}")
        tickets = []
        buildings = []
        
    menu_context = await get_menu_context()
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Archived Maintenance Requests", 
        "status_filter": "archived",
        "current_datetime": datetime.now(),
        **menu_context
    })