from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from ocs_shared_models import User, Building, Room, SystemMessage
from database import get_db, init_database
from services import tickets_service
from management_service import management_service
from service_health import health_checker

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Portal (Python)")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Context processor for menu visibility
async def get_menu_context():
    """Get menu visibility context for templates"""
    try:
        menu_visibility = await health_checker.get_menu_visibility()
        return {"menu_visibility": menu_visibility}
    except Exception as e:
        print(f"Error getting menu context: {e}")
        # Return all menus as visible if health check fails
        return {"menu_visibility": {
            "tickets": True,
            "inventory": True,
            "manage": True,
            "requisitions": True,
            "admin": True
        }}

async def render_template(template_name: str, context: dict):
    """Helper function to render templates with menu context"""
    menu_context = await get_menu_context()
    return templates.TemplateResponse(template_name, {**context, **menu_context})

# Import and setup user/building routes from separate module
try:
    from user_building_routes import setup_user_building_routes
    setup_user_building_routes(app)
    print("✅ User and building routes imported successfully")
except Exception as e:
    print(f"❌ Error importing user/building routes: {e}")

# Homepage route
@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
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
        })()    # Get menu visibility context
    menu_context = await get_menu_context()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "homepage_message": homepage_message,
        **menu_context
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
    
    # Get menu context
    menu_context = await get_menu_context()
    
    return templates.TemplateResponse("tech_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Open Technology Tickets",
        "status_filter": "open",
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
        **menu_context
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
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("tech_ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        **menu_context
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
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("maintenance_tickets_list.html", {
        "request": request,
        "tickets": tickets,
        "buildings": buildings,
        "page_title": "Closed Maintenance Requests",
        "status_filter": "closed",
        **menu_context
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
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("maintenance_ticket_detail.html", {
        "request": request,
        "ticket": ticket,
        **menu_context
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

# Management Routes - communicate with ocs-manage API
@app.get("/manage/settings")
async def manage_settings(request: Request):
    """Display system settings and configuration"""
    try:
        # Get system statistics from manage API
        stats = await management_service.get_system_stats()
        health = await management_service.health_check()
        
        if not stats:
            stats = {
                "users": 0,
                "buildings": 0,
                "rooms": 0,
                "timestamp": "Service unavailable"
            }
            
    except Exception as e:
        print(f"Error fetching management data: {e}")
        stats = {
            "users": 0,
            "buildings": 0,
            "rooms": 0,
            "timestamp": "Error loading data"        }
        health = False
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("manage_settings.html", {
        "request": request,
        "stats": stats,
        "service_health": health,
        **menu_context
    })

@app.get("/manage/logs")
async def manage_logs(request: Request):
    """Display system logs"""
    try:
        # Get system logs from manage API
        logs = await management_service.get_system_logs(limit=50)
        log_stats = await management_service.get_log_stats()
        health = await management_service.health_check()
        
    except Exception as e:
        print(f"Error fetching system logs: {e}")
        logs = []
        log_stats = None
        health = False
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("manage_logs.html", {
        "request": request,
        "logs": logs,
        "log_stats": log_stats,
        "service_health": health,
        "current_time": datetime.now(),
        **menu_context
    })

@app.post("/manage/logs/clear")
async def clear_logs(request: Request):
    """Clear all system logs"""
    try:
        success = await management_service.clear_logs()
        return {"success": success, "message": "Logs cleared successfully" if success else "Failed to clear logs"}
    except Exception as e:
        print(f"Error clearing logs: {e}")
        return {"success": False, "message": str(e)}

@app.get("/manage/other")
async def manage_other(request: Request):
    """Display other management options"""
    try:
        # Get system info from manage API
        stats = await management_service.get_system_stats()
        service_status = await management_service.get_service_status()
        system_stats = await management_service.get_system_performance()
        system_info = await management_service.get_system_info()
        health = await management_service.health_check()
        
    except Exception as e:
        print(f"Error fetching management data: {e}")
        stats = None
        service_status = None
        system_stats = None
        system_info = None
        health = False
    
    menu_context = await get_menu_context()
    return templates.TemplateResponse("manage_other.html", {
        "request": request,
        "stats": stats,
        "service_status": service_status,
        "system_stats": system_stats,
        "system_info": system_info,
        "service_health": health,
        **menu_context
    })

# Additional management API endpoints
@app.post("/manage/maintenance/run")
async def run_maintenance(request: Request):
    """Run system maintenance tasks"""
    try:
        success = await management_service.run_maintenance()
        return {"success": success, "message": "Maintenance completed successfully" if success else "Maintenance failed"}
    except Exception as e:
        print(f"Error running maintenance: {e}")
        return {"success": False, "message": str(e)}

@app.post("/manage/search/rebuild")
async def rebuild_search_index(request: Request):
    """Rebuild search index"""
    try:
        success = await management_service.rebuild_search_index()
        return {"success": success, "message": "Search index rebuilt successfully" if success else "Search index rebuild failed"}
    except Exception as e:
        print(f"Error rebuilding search index: {e}")
        return {"success": False, "message": str(e)}

@app.post("/manage/database/optimize")
async def optimize_databases(request: Request):
    """Optimize all databases"""
    try:
        success = await management_service.optimize_databases()
        return {"success": success, "message": "Database optimization completed successfully" if success else "Database optimization failed"}
    except Exception as e:
        print(f"Error optimizing databases: {e}")
        return {"success": False, "message": str(e)}

@app.get("/manage/test/{service_name}")
async def test_service(service_name: str, request: Request):
    """Test a specific service"""
    try:
        result = await management_service.test_service(service_name)
        return result
    except Exception as e:
        print(f"Error testing service {service_name}: {e}")
        return {"success": False, "message": str(e)}

@app.post("/manage/data/export")
async def export_data(request: Request):
    """Export all system data"""
    try:
        data = await management_service.export_data()
        return Response(content=data, media_type="application/zip", 
                       headers={"Content-Disposition": "attachment; filename=ocs_data_export.zip"})
    except Exception as e:
        print(f"Error exporting data: {e}")
        return {"success": False, "message": str(e)}

@app.post("/manage/data/import")
async def import_data(request: Request, file: UploadFile = File(...)):
    """Import data from uploaded file"""
    try:
        file_data = await file.read()
        success = await management_service.import_data(file_data)
        return {"success": success, "message": "Data imported successfully" if success else "Data import failed"}
    except Exception as e:
        print(f"Error importing data: {e}")
        return {"success": False, "message": str(e)}

@app.post("/manage/reports/generate")
async def generate_reports(request: Request):
    """Generate system reports"""
    try:
        data = await management_service.generate_reports()
        return Response(content=data, media_type="application/pdf", 
                       headers={"Content-Disposition": "attachment; filename=ocs_system_reports.pdf"})
    except Exception as e:
        print(f"Error generating reports: {e}")
        return {"success": False, "message": str(e)}

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
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error getting service status: {e}")
        return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
