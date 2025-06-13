import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from ocs_shared_models import User, Building, Room, SystemMessage
from ocs_shared_models.timezone_utils import central_now, format_central_time
from ocs_shared_models.auth_middleware import AuthMiddleware, get_current_user
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Import authentication routes
from routes.auth_routes import router as auth_router
from routes.admin_auth_routes import router as admin_auth_router
from routes.user_routes import router as user_router
from routes.dashboard_routes import router as dashboard_router

# Include authentication route handlers
app.include_router(auth_router)
app.include_router(admin_auth_router)
app.include_router(user_router)
app.include_router(dashboard_router)

async def get_menu_context(request: Request = None):
    """Get menu visibility context for templates"""
    try:
        menu_visibility = await health_checker.get_menu_visibility()
        
        # If we have a request with an authenticated user, use permissions to refine menu visibility
        user_permissions = {}
        if request and hasattr(request.state, "user"):
            user = request.state.user
            user_permissions = user.get("permissions", {})
            
            # Refine menu visibility based on permissions
            if "tickets" in user_permissions and user_permissions["tickets"] < 1:
                menu_visibility["tickets"] = False
                
            if "inventory" in user_permissions and user_permissions["inventory"] < 1:
                menu_visibility["inventory"] = False
                
            if "purchasing" in user_permissions and user_permissions["purchasing"] < 1:
                menu_visibility["purchasing"] = False
                
            # Admin menu requires admin access to user_management
            if "user_management" not in user_permissions or user_permissions["user_management"] < 3:
                menu_visibility["admin"] = False
        
        print(f"🔍 Dynamic menu context: {menu_visibility}")
        return {"menu_visibility": menu_visibility, "is_authenticated": bool(user_permissions)}
        
    except Exception as e:
        print(f"⚠️ Health checker failed, using fallback menu: {e}")
        # Fallback to show all menus if health checker fails
        return {"menu_visibility": {
            "tickets": True,
            "inventory": True,
            "purchasing": True,
            "manage": True,
            "forms": True,
            "admin": True if request and hasattr(request.state, "user") else False
        }, "is_authenticated": request and hasattr(request.state, "user")}

async def render_template(template_name: str, context: dict):
    """Helper function to render templates with menu context"""
    # Get request object from context if available
    request = context.get("request")
    
    # Pass request to get_menu_context to check authentication status
    menu_context = await get_menu_context(request)
    
    # Add user info to template context if authenticated
    if request and hasattr(request.state, "user"):
        user = request.state.user
        user_context = {
            "user": {
                "name": user.get("name"),
                "email": user.get("email"),
                "roles": user.get("roles", [])
            }
        }
        return templates.TemplateResponse(template_name, {**context, **menu_context, **user_context})
    
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

@app.get("/tickets/maintenance/export")
async def export_maintenance_tickets(request: Request):
    """Export maintenance tickets to CSV"""
    try:
        csv_content = await tickets_service.export_maintenance_tickets_csv()
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f"maintenance_tickets_export_{current_date}.csv"
        
        return Response(
            content=csv_content,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"❌ Error exporting maintenance tickets: {e}")
        # Return to the tickets page with error
        return RedirectResponse("/tickets/maintenance/open", status_code=303)

@app.post("/tickets/maintenance/import")
async def import_maintenance_tickets(request: Request, file: UploadFile = File(...), operation: str = Form(...)):
    """Import maintenance tickets from CSV"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Call the import service
        result = await tickets_service.import_maintenance_tickets_csv(file_content, operation)
        
        print(f"✅ Maintenance tickets import successful: {result}")
        
        # Parse the result to get import count
        import_count = "unknown"
        if result and "imported" in str(result).lower():
            # Try to extract the number from the result
            import re
            match = re.search(r'(\d+)', str(result))
            if match:
                import_count = match.group(1)
        
        return RedirectResponse(f"/tickets/maintenance/open?import_success=true&count={import_count}&mode={operation}", status_code=303)
    except Exception as e:
        print(f"❌ Error importing maintenance tickets: {e}")
        error_msg = str(e).replace("'", "").replace('"', "")[:100]  # Sanitize and limit length
        return RedirectResponse(f"/tickets/maintenance/open?import_error=true&message={error_msg}", status_code=303)

@app.get("/tickets/maintenance/{ticket_id}")
async def view_maintenance_ticket(request: Request, ticket_id: int):
    """View individual maintenance ticket details"""
    try:
        ticket = await tickets_service.get_maintenance_ticket(ticket_id)
        if not ticket:
            return RedirectResponse("/tickets/maintenance/open", status_code=303)
        
        # Get ticket update history
        updates = await tickets_service.get_ticket_updates("maintenance", ticket_id)
        
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
        return RedirectResponse("/tickets/maintenance/open", status_code=303)
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("maintenance_ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        "updates": updates,
        **menu_context
    })

@app.post("/tickets/maintenance/{ticket_id}/update")
async def update_maintenance_ticket_status(
    ticket_id: int,
    status: str = Form(...),
    update_message: str = Form(default="")
):
    """Update maintenance ticket status and add update message via Tickets API"""
    try:
        if update_message.strip():
            update_data = {
                "status": status,
                "update_message": update_message.strip(),
                "updated_by": "System User"  # Replace with actual user when auth is implemented
            }
            success = await tickets_service.update_maintenance_ticket_comprehensive(ticket_id, update_data)
        else:
            success = await tickets_service.update_maintenance_ticket_status(ticket_id, status)
        if success:
            print(f"Maintenance ticket {ticket_id} updated - Status: {status}")
        else:
            print(f"Failed to update maintenance ticket {ticket_id}")
    except Exception as e:
        print(f"Error updating maintenance ticket: {e}")
    return RedirectResponse(f"/tickets/maintenance/{ticket_id}", status_code=303)

# Clear Tickets Routes
@app.post("/tickets/tech/clear")
async def clear_tech_tickets(request: Request):
    """Clear all technology tickets"""
    try:
        result = await tickets_service.clear_all_tech_tickets()
        if result.get("success", True):
            print(f"✅ Tech tickets cleared: {result.get('message', 'Success')}")
        else:
            print(f"❌ Failed to clear tech tickets: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error clearing tech tickets: {e}")
    return RedirectResponse("/tickets/tech/open", status_code=303)

@app.post("/tickets/maintenance/clear")
async def clear_maintenance_tickets(request: Request):
    """Clear all maintenance tickets"""
    try:
        result = await tickets_service.clear_all_maintenance_tickets()
        if result.get("success", True):
            print(f"✅ Maintenance tickets cleared: {result.get('message', 'Success')}")
        else:
            print(f"❌ Failed to clear maintenance tickets: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error clearing maintenance tickets: {e}")
    return RedirectResponse("/tickets/maintenance/open", status_code=303)

# Keep other non-ticket routes (inventory, users, etc.)
@app.get("/inventory/add")
async def add_inventory_form(request: Request):
    menu_context = await get_menu_context()
    return templates.TemplateResponse("add_inventory.html", {
        "request": request,
        **menu_context
    })

@app.post("/inventory/add")
async def add_inventory_submit(request: Request):
    menu_context = await get_menu_context()
    return templates.TemplateResponse("inventory_success.html", {
        "request": request,
        **menu_context
    })

@app.get("/tickets/success")
async def ticket_success(request: Request):
    menu_context = await get_menu_context()
    return templates.TemplateResponse("ticket_success.html", {
        "request": request,
        **menu_context
    })

# Management Routes - Device Register
@app.get("/manage/device-register")
async def device_register(request: Request):
    """Device register page with inventory management and dual checkout system"""
    try:
        # Import necessary items from the management service
        from management_service import management_service
        
        # Get buildings and users for the form
        buildings = await management_service.get_buildings()
        users = await management_service.get_users()
        inventory_items = await management_service.get_inventory_items()
        
        menu_context = await get_menu_context()
        return templates.TemplateResponse("device_register.html", {
            "request": request,
            "buildings": buildings,
            "users": users,
            "inventory_items": inventory_items,
            **menu_context
        })
    except Exception as e:
        print(f"Error loading device register: {e}")
        menu_context = await get_menu_context()
        return templates.TemplateResponse("device_register.html", {
            "request": request,
            "buildings": [],
            "users": [],
            "inventory_items": [],
            **menu_context
        })

# Forms Routes
@app.get("/forms/time")
async def time_forms(request: Request):
    """Time forms management page"""
    try:
        menu_context = await get_menu_context()
        return templates.TemplateResponse("forms/time.html", {
            "request": request,
            **menu_context
        })
    except Exception as e:
        print(f"Error loading time forms: {e}")
        return RedirectResponse("/", status_code=303)

@app.get("/forms/fuel")
async def fuel_tracking(request: Request):
    """Fuel tracking management page"""
    try:
        menu_context = await get_menu_context()
        return templates.TemplateResponse("forms/fuel.html", {
            "request": request,
            **menu_context
        })
    except Exception as e:
        print(f"Error loading fuel tracking: {e}")
        return RedirectResponse("/", status_code=303)

# Purchasing Routes
@app.get("/purchasing/requisitions")
async def requisitions_page(request: Request):
    """Requisitions management page"""
    try:
        requisitions = await purchasing_service.get_requisitions()
        menu_context = await get_menu_context()
        return templates.TemplateResponse("purchasing/requisitions.html", {
            "request": request,
            "requisitions": requisitions,
            **menu_context
        })
    except Exception as e:
        print(f"Error loading requisitions: {e}")
        return RedirectResponse("/", status_code=303)

@app.get("/purchasing/purchase-orders")
async def purchase_orders_page(request: Request):
    """Purchase Orders management page"""
    try:
        purchase_orders = await purchasing_service.get_purchase_orders()
        menu_context = await get_menu_context()
        return templates.TemplateResponse("purchasing/purchase_orders.html", {
            "request": request,
            "purchase_orders": purchase_orders,
            **menu_context
        })
    except Exception as e:
        print(f"Error loading purchase orders: {e}")
        return RedirectResponse("/", status_code=303)

@app.get("/purchasing/requisitions/new")
async def new_requisition_page(request: Request):
    """Create new requisition page"""
    try:
        buildings = await tickets_service.get_buildings()  # Reuse buildings API from tickets
        menu_context = await get_menu_context()
        return templates.TemplateResponse("purchasing/new_requisition.html", {
            "request": request,
            "buildings": buildings,
            **menu_context
        })
    except Exception as e:
        print(f"Error loading new requisition form: {e}")
        return RedirectResponse("/", status_code=303)

@app.post("/purchasing/requisitions/new")
async def create_requisition(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    department: str = Form(...),
    requested_by: str = Form(...),
    estimated_cost: str = Form(None),
    justification: str = Form(None),
    priority: str = Form("normal"),
    building_id: int = Form(None)
):
    """Create a new requisition"""
    try:
        requisition_data = {
            "title": title,
            "description": description,
            "department": department,
            "requested_by": requested_by,
            "estimated_cost": estimated_cost,
            "justification": justification,
            "priority": priority,
            "building_id": building_id
        }
        
        result = await purchasing_service.create_requisition(requisition_data)
        if result:
            return RedirectResponse("/purchasing/requisitions", status_code=303)
        else:
            # Handle error case
            return RedirectResponse("/purchasing/requisitions/new", status_code=303)
    except Exception as e:
        print(f"Error creating requisition: {e}")
        return RedirectResponse("/purchasing/requisitions/new", status_code=303)

@app.get("/purchasing/purchase-orders/new")
async def new_purchase_order_page(request: Request):
    """Create new purchase order page"""
    try:
        # Get approved requisitions for selection
        approved_requisitions = await purchasing_service.get_requisitions(status_filter="approved")
        menu_context = await get_menu_context()
        return templates.TemplateResponse("purchasing/new_purchase_order.html", {
            "request": request,
            "approved_requisitions": approved_requisitions,
            **menu_context
        })
    except Exception as e:
        print(f"Error loading new purchase order form: {e}")
        return RedirectResponse("/", status_code=303)

@app.post("/purchasing/purchase-orders/new")
async def create_purchase_order(
    request: Request,
    po_number: str = Form(...),
    requisition_id: int = Form(None),
    vendor_name: str = Form(...),
    vendor_contact: str = Form(None),
    total_amount: str = Form(None),
    description: str = Form(None),
    delivery_address: str = Form(None),
    created_by: str = Form(...)
):
    """Create a new purchase order"""
    try:
        po_data = {
            "po_number": po_number,
            "requisition_id": requisition_id,
            "vendor_name": vendor_name,
            "vendor_contact": vendor_contact,
            "total_amount": total_amount,
            "description": description,
            "delivery_address": delivery_address,
            "created_by": created_by
        }
        
        result = await purchasing_service.create_purchase_order(po_data)
        if result:
            return RedirectResponse("/purchasing/purchase-orders", status_code=303)
        else:
            # Handle error case
            return RedirectResponse("/purchasing/purchase-orders/new", status_code=303)
    except Exception as e:
        print(f"Error creating purchase order: {e}")
        return RedirectResponse("/purchasing/purchase-orders/new", status_code=303)

# Health check and service status endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for the portal"""
    return {"status": "healthy", "service": "portal"}

@app.get("/api/services/status")
async def get_services_status():
    """Get status of all microservices"""
    try:
        menu_visibility = await health_checker.get_menu_visibility()
        service_status = await health_checker.get_service_health()
        return {
            "menu_visibility": menu_visibility,
            "service_status": service_status,
            "timestamp": central_now().isoformat()
        }
    except Exception as e:
        print(f"Error getting service status: {e}")
        return {"error": str(e), "timestamp": central_now().isoformat()}
