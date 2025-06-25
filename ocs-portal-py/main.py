"""
OCS Tracker Portal with Azure AD Authentication
"""
import sys
import os
import re
import uvicorn
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import httpx
import json
from ocs_shared_models import User, Building, Room, SystemMessage
from ocs_shared_models.timezone_utils import central_now, format_central_time
from database import get_db, init_database
from services import get_service_for_request
from management_service import management_service
from service_health import health_checker
from health_router import router as health_router

# Initialize database on startup
try:
    init_database()
except Exception as e:
    print(f"⚠️ Database initialization failed: {e}")
    print("🔄 Starting application without database connection")

# Import authentication components
from auth_config import AuthConfig
from auth_middleware import AuthenticationMiddleware, get_current_user, get_menu_context as auth_get_menu_context
from auth_routes import auth_router
from database import get_db

# Service URLs - get from environment or use defaults
TICKETS_API_URL = os.getenv("TICKETS_API_URL", "http://ocs-tickets-api:8000")
PURCHASING_API_URL = os.getenv("PURCHASING_API_URL", "http://ocs-purchasing-api:8000")
MANAGE_API_URL = os.getenv("MANAGE_API_URL", "http://ocs-manage-api:8000")
FORMS_API_URL = os.getenv("FORMS_API_URL", "http://ocs-forms-api:8000")

# Import existing components
try:
    from ocs_shared_models import User, Building, Room, SystemMessage
    from ocs_shared_models.timezone_utils import central_now, format_central_time
except ImportError:
    sys.path.insert(0, '../ocs_shared_models')
    from models import User, Building, Room, SystemMessage
    from timezone_utils import central_now, format_central_time

# Initialize FastAPI app
app = FastAPI(title="OCS Tracker Portal", description="Obion County Schools Management Portal")

# Add session middleware for OAuth state management
app.add_middleware(SessionMiddleware, secret_key=AuthConfig.JWT_SECRET)

# Add authentication middleware (but exclude auth routes)
app.add_middleware(
    AuthenticationMiddleware,
    exclude_paths=[
        "/",  # Allow home page to handle its own authentication
        "/auth/login", 
        "/auth/microsoft", 
        "/auth/callback",
        "/auth/status",
        "/static",
        "/health",
        "/docs",
        "/openapi.json",
        "/users/list",  # Allow redirect to new admin interface
        "/users"        # Allow redirect to new admin interface
    ]
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include authentication routes
app.include_router(auth_router)

# Include health router
app.include_router(health_router)

# Include user import routes
try:
    from user_import_routes import router as user_import_router
    app.include_router(user_import_router)
    print("✅ User import routes loaded successfully")
except ImportError as e:
    print(f"⚠️ User import routes not available: {e}")
except Exception as e:
    print(f"❌ Error loading user import routes: {e}")

# Include scheduler routes
try:
    from scheduler_routes import router as scheduler_router, set_scheduler_service
    from scheduler_service import SchedulerService
    
    # Create global scheduler instance
    scheduler_service = SchedulerService()
    set_scheduler_service(scheduler_service)
    
    app.include_router(scheduler_router)
    print("✅ Scheduler routes loaded successfully")
except ImportError as e:
    print(f"⚠️ Scheduler routes not available: {e}")
    scheduler_service = None
except Exception as e:
    print(f"❌ Error loading scheduler routes: {e}")
    scheduler_service = None

# Include notification routes
try:
    from notification_routes import setup_notification_routes
    setup_notification_routes(app)
    print("✅ Notification routes loaded successfully")
except ImportError as e:
    print(f"⚠️ Notification routes not available: {e}")
except Exception as e:
    print(f"❌ Error loading notification routes: {e}")

async def get_menu_context(request: Request = None):
    """Get menu visibility context for templates - using role-based filtering"""
    try:
        if request:
            # Use the role-based menu context from auth middleware
            return await auth_get_menu_context(request)
        else:
            # No request, return guest context
            return {
                'user': None,
                'access_level': 'guest',
                'permissions': {},
                'menu_visibility': {},
                'menu_items': [],
                'is_authenticated': False
            }
    except Exception as e:
        print(f"⚠️ Menu context failed: {e}")
        # Fallback to show limited menus
        return {
            'user': None,
            'access_level': 'guest',
            'permissions': {},
            'menu_visibility': {
                "tickets": True,
                "inventory": False,
                "purchasing": False,
                "manage": False,
                "forms": False,
                "admin": False
            },
            'menu_items': [],
            'is_authenticated': False
        }

async def render_template(template_name: str, context: dict):
    """Helper function to render templates with menu context"""
    # Get request object from context if available
    request = context.get("request")
    menu_context = await get_menu_context(request)
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
    """Home page with editable system message and dashboard - requires authentication"""
    # Check if user is authenticated
    user = get_current_user(request)
    
    if not user:
        # User not authenticated, redirect to login
        return RedirectResponse(url="/auth/login", status_code=302)
    
    # Initialize default values
    homepage_message = None
    dashboard_data = {
        "tickets": {
            "tech_open": 0,
            "tech_closed": 0,
            "maintenance_open": 0,
            "maintenance_closed": 0,
            "total_open": 0,
            "total_closed": 0
        }
    }
    menu_context = {
        'user': user,
        'access_level': user.get('access_level', 'guest'),
        'permissions': user.get('permissions', {}),
        'menu_visibility': {},
        'menu_items': [],
        'is_authenticated': True
    }
    
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
        # Create a default message instead of redirecting
        homepage_message = type('SystemMessage', (), {
            'content': "Welcome to OCS Tracker Portal. Please check with your administrator if you continue to see this message.",
            'message_type': 'homepage'
        })()
        
    # Gather dashboard data
    try:
        dashboard_data = await get_dashboard_data(db, request)
    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        # Use default dashboard data instead of redirecting
        
    # Get menu visibility context
    try:
        menu_context = await get_menu_context(request)
    except Exception as e:
        print(f"Error getting menu context: {e}")
        # Use default menu context instead of redirecting
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "homepage_message": homepage_message,
        "dashboard_data": dashboard_data,
        **menu_context
    })

async def get_dashboard_data(db: Session, request: Request):
    """Gather data for dashboard charts"""
    try:
        # Get authenticated service instances for this request
        services = get_service_for_request(request)
        tickets_svc = services["tickets"]
        
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
            tech_open = await tickets_svc.get_tech_tickets("open")
            tech_closed = await tickets_svc.get_tech_tickets("closed")
            maintenance_open = await tickets_svc.get_maintenance_tickets("open")
            maintenance_closed = await tickets_svc.get_maintenance_tickets("closed")
            
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
            # Pass the auth token to health checker if applicable
            session_token = request.cookies.get("session_token")
            dashboard["service_health"] = await health_checker.get_service_health(auth_token=session_token)
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
        # Get services with authentication token
        services = get_service_for_request(request)
        buildings = await services["tickets"].get_buildings()
    except Exception as e:
        print(f"Error fetching buildings: {e}")
        buildings = []    
    # Get menu context with session token
    menu_context = await get_menu_context(request)
    
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
    description: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Process technology ticket submission via Tickets API"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        # Get building and room names
        buildings = await services["tickets"].get_buildings()
        building_obj = next((b for b in buildings if b["id"] == building), None)
        
        rooms = await services["tickets"].get_building_rooms(building)
        room_obj = next((r for r in rooms if r["id"] == room), None)
        
        ticket_data = {
            "title": title,
            "description": description,
            "issue_type": issue_type,
            "building_name": building_obj["name"] if building_obj else "Unknown",
            "room_name": room_obj["name"] if room_obj else "Unknown",
            "tag": tag,
            "created_by": f"{current_user.first_name} {current_user.last_name}"
        }
        
        result = await services["tickets"].create_tech_ticket(ticket_data)
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
        # Get authenticated service instance for this request
        services = get_service_for_request(request)
        tickets_svc = services["tickets"]
        
        tickets = await tickets_svc.get_tech_tickets("open")
        buildings = await tickets_svc.get_buildings()
        closed_count = await tickets_svc.get_closed_tickets_count("tech")
        
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
    menu_context = await get_menu_context(request)
    
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
        # Get services with authentication token
        services = get_service_for_request(request)
        
        tickets = await services["tickets"].get_tech_tickets("closed")
        buildings = await services["tickets"].get_buildings()
        
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
    
    menu_context = await get_menu_context(request)
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
        # Get services with authentication token
        services = get_service_for_request(request)
        
        csv_content = await services["tickets"].export_tech_tickets_csv()
        
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

@app.get("/tickets/maintenance/export")
async def export_maintenance_tickets(request: Request):
    """Export maintenance tickets to CSV"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        csv_content = await services["tickets"].export_maintenance_tickets_csv()
        
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
        # Return to the tickets page with error        return RedirectResponse("/tickets/maintenance/open", status_code=303)

# CSV Import Routes
@app.post("/tickets/tech/import")
async def import_tech_tickets(request: Request, file: UploadFile = File(...), operation: str = Form(...)):
    """Import tech tickets from CSV"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        # Read file content
        file_content = await file.read()
        
        # Call the import service with filename
        result = await services["tickets"].import_tech_tickets_csv(file_content, file.filename, operation)
        
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

@app.post("/tickets/maintenance/import")
async def import_maintenance_tickets(request: Request, file: UploadFile = File(...), operation: str = Form(...)):
    """Import maintenance tickets from CSV"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        # Read file content
        file_content = await file.read()
          # Call the import service with filename
        result = await services["tickets"].import_maintenance_tickets_csv(file_content, file.filename, operation)
        
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

# Archive routes must come before parameterized routes
@app.get("/tickets/tech/archives")
async def tech_tickets_archives(
    request: Request,
    archive: Optional[str] = None,
    status_filter: Optional[str] = None
):
    """Display tech ticket archives using main template with archive selector"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        # Get list of available archives
        archives = await services["tickets"].get_tech_archives()
        
        tickets = []
        selected_archive = None
        archive_info = {}
        
        # If an archive is selected, get its tickets
        if archive:
            archive_data = await services["tickets"].get_tech_archive_tickets(archive, status_filter)
            tickets = archive_data.get("tickets", [])
            selected_archive = archive
            archive_info = next((a for a in archives if a["name"] == archive), {})
            
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
        
        buildings = await services["tickets"].get_buildings()
        
        # Get closed tickets count for consistency
        closed_count = 0
        try:
            closed_response = await services["tickets"].get_closed_tech_tickets()
            if isinstance(closed_response, dict) and "tickets" in closed_response:
                closed_count = len(closed_response["tickets"])
        except:
            pass
            
    except Exception as e:
        print(f"Error fetching tech archive tickets: {e}")
        tickets = []
        buildings = []
        archives = []
        closed_count = 0
    
    menu_context = await get_menu_context(request)
    return templates.TemplateResponse("tech_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Technology Ticket Archives",
        "status_filter": "archived",
        "archives": archives,
        "selected_archive": selected_archive,
        "archive_info": archive_info,
        "closed_count": closed_count,
        "current_datetime": datetime.now(),
        **menu_context
    })

@app.get("/tickets/maintenance/archives")
async def maintenance_tickets_archives(
    request: Request,
    archive: Optional[str] = None,
    status_filter: Optional[str] = None
):
    """Display maintenance ticket archives using main template with archive selector"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        # Get list of available archives
        archives = await services["tickets"].get_maintenance_archives()
        
        tickets = []
        selected_archive = None
        archive_info = {}
        buildings = []
        closed_count = 0
        
        # If an archive is selected, get its tickets
        if archive:
            archive_data = await services["tickets"].get_maintenance_archive_tickets(archive, status_filter)
            tickets = archive_data.get("tickets", [])
            selected_archive = archive
            archive_info = next((a for a in archives if a["name"] == archive), {})
            
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
        
        buildings = await services["tickets"].get_buildings()
        
        # Get closed tickets count for consistency
        try:
            closed_response = await services["tickets"].get_closed_maintenance_tickets()
            if isinstance(closed_response, dict) and "tickets" in closed_response:
                closed_count = len(closed_response["tickets"])
        except:
            pass
            
    except Exception as e:
        print(f"Error fetching maintenance archive tickets: {e}")
        tickets = []
        buildings = []
        archives = []
        closed_count = 0
    
    menu_context = await get_menu_context(request)
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Maintenance Ticket Archives",
        "status_filter": "archived",
        "archives": archives,
        "selected_archive": selected_archive,
        "archive_info": archive_info,
        "closed_count": closed_count,
        "current_datetime": datetime.now(),
        **menu_context
    })

# Clear All Tickets Routes - Must come before parameterized routes
# Portal acts as a thin proxy - delegates to tickets module for business logic
@app.post("/tickets/tech/clear")
async def clear_tech_tickets_proxy(request: Request, user: dict = Depends(get_current_user)):
    """Proxy clear tech tickets request to tickets module"""
    try:
        # Forward request directly to tickets API with auth
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create auth headers for the tickets API
            headers = {
                "Authorization": f"Bearer {user.get('token', '')}", 
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                f"{TICKETS_API_URL}/api/tickets/tech/clear",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Tech tickets cleared via proxy: {result}")
                return RedirectResponse("/tickets/tech/open?message=Tech tickets cleared successfully", status_code=303)
            else:
                print(f"❌ Tickets API error: {response.status_code} - {response.text}")
                return RedirectResponse("/tickets/tech/open?error=Failed to clear tickets", status_code=303)
        
    except Exception as e:
        print(f"❌ Error proxying clear tech tickets request: {e}")
        return RedirectResponse("/tickets/tech/open?error=Failed to clear tickets", status_code=303)

@app.post("/tickets/maintenance/clear")
async def clear_maintenance_tickets_proxy(request: Request, user: dict = Depends(get_current_user)):
    """Proxy clear maintenance tickets request to tickets module"""
    try:
        # Forward request directly to tickets API with auth
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create auth headers for the tickets API
            headers = {
                "Authorization": f"Bearer {user.get('token', '')}", 
                "Content-Type": "application/json"
            }
            
            response = await client.post(
                f"{TICKETS_API_URL}/api/tickets/maintenance/clear",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Maintenance tickets cleared via proxy: {result}")
                return RedirectResponse("/tickets/maintenance/open?message=Maintenance tickets cleared successfully", status_code=303)
            else:
                print(f"❌ Tickets API error: {response.status_code} - {response.text}")
                return RedirectResponse("/tickets/maintenance/open?error=Failed to clear tickets", status_code=303)
        
    except Exception as e:
        print(f"❌ Error proxying clear maintenance tickets request: {e}")
        return RedirectResponse("/tickets/maintenance/open?error=Failed to clear tickets", status_code=303)

# Parameterized routes - Must come after specific routes
@app.get("/tickets/tech/{ticket_id}")
async def view_tech_ticket(request: Request, ticket_id: int):
    """View individual technology ticket details"""
    try:
        # Get authenticated service instance for this request
        services = get_service_for_request(request)
        tickets_svc = services["tickets"]
        
        ticket = await tickets_svc.get_tech_ticket(ticket_id)
        if not ticket:
            return RedirectResponse("/tickets/tech/open", status_code=303)
        
        # Get ticket update history
        updates = await tickets_svc.get_ticket_updates("tech", ticket_id)
        
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
    
    menu_context = await get_menu_context(request)
    return templates.TemplateResponse("tech_ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        "updates": updates,
        **menu_context
    })

@app.post("/tickets/tech/{ticket_id}/update")
async def update_tech_ticket_status(
    request: Request,
    ticket_id: int,
    status: str = Form(...),
    update_message: str = Form(default=""),
    current_user: User = Depends(get_current_user)
):
    """Update technology ticket status and add update message via Tickets API"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        if update_message.strip():
            update_data = {
                "status": status,
                "update_message": update_message.strip(),
                "updated_by": f"{current_user.first_name} {current_user.last_name}"
            }
            success = await services["tickets"].update_tech_ticket_comprehensive(ticket_id, update_data)
        else:
            success = await services["tickets"].update_tech_ticket_status(ticket_id, status)
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
        # Get services with authentication token
        services = get_service_for_request(request)
        
        buildings = await services["tickets"].get_buildings()
    except Exception as e:
        print(f"Error fetching buildings: {e}")
        buildings = []
    
    # Get menu context
    menu_context = await get_menu_context(request)
    
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
    description: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Process maintenance ticket submission via Tickets API"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        # Get building and room names
        buildings = await services["tickets"].get_buildings()
        building_obj = next((b for b in buildings if b["id"] == building), None)
        
        rooms = await services["tickets"].get_building_rooms(building)
        room_obj = next((r for r in rooms if r["id"] == room), None)          # Combine room and specific location for better context
        location_details = room_obj["name"] if room_obj else "Unknown"
        
        ticket_data = {
            "title": title,
            "description": description,
            "issue_type": issue_type,
            "building_name": building_obj["name"] if building_obj else "Unknown",
            "room_name": location_details,
            "created_by": f"{current_user.first_name} {current_user.last_name}"        }
        
        result = await services["tickets"].create_maintenance_ticket(ticket_data)
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
        # Get authenticated service instance for this request
        services = get_service_for_request(request)
        tickets_svc = services["tickets"]
        
        tickets = await tickets_svc.get_maintenance_tickets("open")
        buildings = await tickets_svc.get_buildings()
        closed_count = await tickets_svc.get_closed_tickets_count("maintenance")
        
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
    menu_context = await get_menu_context(request)
    
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
        # Get services with authentication token
        services = get_service_for_request(request)
        
        tickets = await services["tickets"].get_maintenance_tickets("closed")
        buildings = await services["tickets"].get_buildings()
        
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
                        date_str += ":00"
                    # Remove Z timezone and add UTC offset
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
    
    menu_context = await get_menu_context(request)
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Closed Maintenance Requests",
        "status_filter": "closed",
        "current_datetime": datetime.now(),
        **menu_context
    })

# Roll Database Routes
@app.post("/tickets/tech/roll-database")
async def roll_tech_database(request: Request, archive_name: str = Form(...)):
    """Roll the tech database - archive current tickets and create new empty table"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        result = await services["tickets"].roll_tech_database(archive_name)
        if result.get("success"):
            redirect_url = "/tickets/tech/open?roll_success=true&archive_name=" + archive_name
        else:
            error_message = result.get("message", "Unknown error")
            redirect_url = f"/tickets/tech/open?roll_error=true&message={error_message}"
        return RedirectResponse(redirect_url, status_code=303)
    except Exception as e:
        print(f"Error rolling tech database: {e}")
        return RedirectResponse(
            f"/tickets/tech/open?roll_error=true&message={str(e)}", 
            status_code=303
        )

@app.post("/tickets/maintenance/roll-database")
async def roll_maintenance_database(request: Request, archive_name: str = Form(...)):
    """Roll the maintenance database - archive current tickets and create new empty table"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        result = await services["tickets"].roll_maintenance_database(archive_name)
        if result.get("success"):
            redirect_url = "/tickets/maintenance/open?roll_success=true&archive_name=" + archive_name
        else:
            error_message = result.get("message", "Unknown error")
            redirect_url = f"/tickets/maintenance/open?roll_error=true&message={error_message}"
        return RedirectResponse(redirect_url, status_code=303)
    except Exception as e:
        print(f"Error rolling maintenance database: {e}")
        return RedirectResponse(
            f"/tickets/maintenance/open?roll_error=true&message={str(e)}", 
            status_code=303
        )

@app.get("/tickets/tech/archives/{archive_name}/delete")
async def delete_tech_archive(request: Request, archive_name: str):
    """Delete a tech ticket archive"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        result = await services["tickets"].delete_tech_archive(archive_name)
        return result
    except Exception as e:
        return {"success": False, "message": f"Error deleting archive: {str(e)}"}

@app.get("/tickets/maintenance/archives/{archive_name}/delete")
async def delete_maintenance_archive(request: Request, archive_name: str):
    """Delete a maintenance ticket archive"""
    try:
        # Get services with authentication token
        services = get_service_for_request(request)
        
        result = await services["tickets"].delete_maintenance_archive(archive_name)
        return result
    except Exception as e:
        return {"success": False, "message": f"Error deleting archive: {str(e)}"}

# User management dashboard functions
async def login_page(request: Request):
    """Display login page"""
    return templates.TemplateResponse("login.html", {"request": request})

# Dashboard (requires authentication)
@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page - requires authentication"""
    print(f"DEBUG: Dashboard route called")
    print(f"DEBUG: Request state user exists: {hasattr(request.state, 'user')}")
    print(f"DEBUG: Session token cookie: {request.cookies.get('session_token', 'None')}")
    
    user = get_current_user(request)
    print(f"DEBUG: get_current_user returned: {user}")
    if not user:
        print("DEBUG: Dashboard - no user found, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=302)
    
    print(f"DEBUG: Dashboard - user {user.get('email')} has access")
    
    try:
        # Get homepage message
        homepage_message = db.query(SystemMessage).filter(
            SystemMessage.message_type == 'homepage'
        ).first()
        
        if not homepage_message:
            default_message = "Welcome to the OCS Tracker Portal. Use the navigation menu to access the available services based on your permissions."
            homepage_message = SystemMessage(
                message_type='homepage',
                content=default_message,
                created_by='System'
            )
            db.add(homepage_message)
            db.commit()
            db.refresh(homepage_message)
        
        # Determine available services based on user permissions
        permissions = user.get('permissions', {})
        available_services = []
        
        if permissions.get('tickets_access', 'none') != 'none':
            available_services.append({
                'name': 'Technology Tickets',
                'description': 'Submit and manage technology support requests',
                'url': '/tickets',
                'icon': '🖥️'
            })
            available_services.append({
                'name': 'Maintenance Tickets', 
                'description': 'Submit and track maintenance requests',
                'url': '/maintenance',
                'icon': '🔧'
            })        
        if permissions.get('manage_access', 'none') != 'none' or permissions.get('inventory_access', 'none') != 'none':
            available_services.append({
                'name': 'Management & Inventory',
                'description': 'Manage buildings, rooms, and inventory',
                'url': '/manage',
                'icon': '📦'
            })
        
        if permissions.get('purchasing_access', 'none') != 'none':
            available_services.append({
                'name': 'Purchase Requisitions',
                'description': 'Submit and track purchase requests',
                'url': '/purchasing',
                'icon': '🛒'
            })
        
        if permissions.get('forms_access', 'none') != 'none':
            available_services.append({
                'name': 'Forms & Documents',
                'description': 'Access district forms and documentation',
                'url': '/forms',
                'icon': '📋'
            })
        
        # Admin services for elevated users
        if user.get('access_level') in ['admin', 'super_admin']:
            available_services.append({
                'name': 'User Management',
                'description': 'Manage users and permissions',
                'url': '/admin/users',
                'icon': '👥'
            })
            available_services.append({
                'name': 'System Administration',
                'description': 'System configuration and management',
                'url': '/admin/system',
                'icon': '⚙️'
            })
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user,
            "homepage_message": homepage_message,
            "available_services": available_services,
            "permissions": permissions
        })
        
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Dashboard loading error")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ocs-portal", "authentication": "enabled"}

# API endpoint to get current user info
@app.get("/api/user")
async def get_current_user_info(request: Request):
    """Get current authenticated user information"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "access_level": user.get("access_level"),
        "permissions": user.get("permissions", {})
    }

# Microservice integration routes
@app.get("/tickets")
async def tickets_service_integration(request: Request):
    """Integrate with ocs-tickets-api service"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    # Check permissions
    permissions = user.get('permissions', {})
    if permissions.get('tickets_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No tickets permission")
    
    # Redirect to tickets API
    return RedirectResponse(url=f"{TICKETS_API_URL}/", status_code=302)

@app.get("/tickets/tech/new")
async def new_tech_ticket_integration(request: Request):
    """Integrate with ocs-tickets-api for new tech tickets"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    permissions = user.get('permissions', {})
    if permissions.get('tickets_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No tickets permission")
    
    # Redirect to tickets API new ticket form
    return RedirectResponse(url=f"{TICKETS_API_URL}/new-ticket", status_code=302)

@app.get("/tickets/maintenance/new") 
async def new_maintenance_ticket_integration(request: Request):
    """Integrate with ocs-tickets-api for new maintenance tickets"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    permissions = user.get('permissions', {})
    if permissions.get('tickets_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No tickets permission")
    
    # Redirect to tickets API maintenance form
    return RedirectResponse(url=f"{TICKETS_API_URL}/new-maintenance-ticket", status_code=302)

@app.get("/maintenance")
async def maintenance_service_integration(request: Request):
    """Integrate with maintenance tickets in ocs-tickets-api"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    permissions = user.get('permissions', {})
    if permissions.get('tickets_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No tickets permission")
    
    # Redirect to tickets API maintenance section
    return RedirectResponse(url=f"{TICKETS_API_URL}/maintenance", status_code=302)

@app.get("/manage")
async def manage_service_integration(request: Request):
    """Integrate with ocs-manage-api service for management and inventory functions"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    permissions = user.get('permissions', {})
    if permissions.get('manage_access', 'none') == 'none' and permissions.get('inventory_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No management or inventory permission")
    
    # Redirect to manage API
    return RedirectResponse(url=f"{MANAGE_API_URL}/", status_code=302)

@app.get("/inventory")
async def inventory_service_integration(request: Request):
    """Integrate with inventory functionality (now part of ocs-manage-api)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    permissions = user.get('permissions', {})
    if permissions.get('inventory_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No inventory permission")
    
    # Get inventory items from manage API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MANAGE_API_URL}/api/inventory")
            if response.status_code == 200:
                inventory_items = response.json()
            else:
                inventory_items = []
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        inventory_items = []
    
    menu_context = auth_get_menu_context(user)
    return templates.TemplateResponse("view_inventory.html", {
        "request": request,
        "user": user,
        "inventory_items": inventory_items,
        **menu_context
    })

@app.get("/inventory/add")
async def add_inventory_form(request: Request):
    """Show add inventory form"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    permissions = user.get('permissions', {})
    if permissions.get('inventory_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No inventory permission")
    
    menu_context = auth_get_menu_context(user)
    return templates.TemplateResponse("add_inventory.html", {
        "request": request,
        "user": user,
        **menu_context
    })

@app.post("/inventory/add")
async def add_inventory_submit(
    request: Request,
    tag: str = Form(...),
    type: str = Form(...),
    brand: str = Form(...),
    model: str = Form(...),
    serial: str = Form(...),
    po_number: str = Form(...),
    price: float = Form(...),
    purchase_date: str = Form(...),
    funds: str = Form(...),
    vendor: str = Form(...),
    school: str = Form(...),    room: str = Form(...)
):
    """Submit new inventory item to manage API"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    permissions = user.get('permissions', {})
    if permissions.get('inventory_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No inventory permission")
    
    # Prepare data for manage API
    inventory_data = {
        "tag_number": tag,
        "item_type": type,
        "brand": brand,
        "model": model,
        "serial_number": serial,
        "purchase_order": po_number,
        "price": str(price),
        "purchase_date": purchase_date,
        "funds": funds,
        "vendor": vendor,
        "description": f"School: {school}, Room: {room}",
        "condition": "excellent",
        "status": "available"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MANAGE_API_URL}/api/inventory", json=inventory_data)
            if response.status_code == 200:
                menu_context = auth_get_menu_context(user)
                return templates.TemplateResponse("inventory_success.html", {
                    "request": request,
                    "user": user,
                    "message": "Inventory item added successfully!",
                    **menu_context
                })
            else:
                raise HTTPException(status_code=400, detail="Failed to add inventory item")
    except Exception as e:
        print(f"Error adding inventory: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/inventory/edit/{item_id}")
async def edit_inventory_form(request: Request, item_id: int):
    """Show edit inventory form"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    permissions = user.get('permissions', {})
    if permissions.get('inventory_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No inventory permission")
    
    # Get inventory item from manage API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MANAGE_API_URL}/api/inventory/{item_id}")
            if response.status_code == 200:
                inventory_item = response.json()
            else:
                raise HTTPException(status_code=404, detail="Inventory item not found")
    except Exception as e:
        print(f"Error fetching inventory item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    menu_context = auth_get_menu_context(user)
    return templates.TemplateResponse("edit_inventory.html", {
        "request": request,
        "user": user,
        "inventory_item": inventory_item,
        **menu_context
    })

@app.post("/inventory/edit/{item_id}")
async def edit_inventory_submit(
    request: Request,
    item_id: int,
    tag: str = Form(...),
    type: str = Form(...),
    brand: str = Form(...),
    model: str = Form(...),
    serial: str = Form(...),
    po_number: str = Form(...),
    price: float = Form(...),
    purchase_date: str = Form(...),
    funds: str = Form(...),
    vendor: str = Form(...),
    school: str = Form(...),
    room: str = Form(...)
):
    """Submit inventory item updates to manage API"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")
    
    permissions = user.get('permissions', {})
    if permissions.get('inventory_access', 'none') == 'none':
        raise HTTPException(status_code=403, detail="Access denied: No inventory permission")
      # Prepare data for manage API
    inventory_data = {
        "tag_number": tag,
        "item_type": type,
        "brand": brand,
        "model": model,
        "serial_number": serial,
        "purchase_order": po_number,
        "price": str(price),
        "purchase_date": purchase_date,
        "funds": funds,
        "vendor": vendor,
        "description": f"School: {school}, Room: {room}",
        "condition": "excellent",
        "status": "available"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{MANAGE_API_URL}/api/inventory/{item_id}", json=inventory_data)
            if response.status_code == 200:
                return RedirectResponse(url="/inventory", status_code=302)
            else:
                raise HTTPException(status_code=400, detail="Failed to update inventory item")
    except Exception as e:
        print(f"Error updating inventory: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
