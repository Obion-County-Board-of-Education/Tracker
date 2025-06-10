"""
User and Building Management Routes
This module contains the working routes for user and building management
"""

from fastapi import Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ocs_shared_models import User, Building, Room
from database import get_db

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Import menu context helper - will be set by main.py
get_menu_context = None
render_template = None

def setup_user_building_routes(app, menu_context_func, render_template_func):
    """Setup user and building management routes"""
    
    # Set module-level references to menu context functions
    global get_menu_context, render_template
    get_menu_context = menu_context_func
    render_template = render_template_func
    
    # Redirect routes for base paths
    @app.get("/users")
    async def users_redirect(request: Request):
        """Redirect /users to /users/list"""
        return RedirectResponse(url="/users/list", status_code=302)
    
    @app.get("/buildings")
    async def buildings_redirect(request: Request):
        """Redirect /buildings to /buildings/list"""
        return RedirectResponse(url="/buildings/list", status_code=302)
    
    @app.get("/users/list")
    async def users_list(request: Request, db: Session = Depends(get_db)):
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
                    "role": (user.roles or 'basic').title(),
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
        
        return await render_template("users.html", {"request": request, "users": users_data})

    @app.get("/buildings/list")
    async def buildings_list(request: Request, db: Session = Depends(get_db)):
        """List all buildings with their room counts, sorted alphabetically by name"""
        try:
            buildings = db.query(Building).order_by(Building.name).all()
            buildings_data = []
            for building in buildings:
                room_count = len(building.rooms) if building.rooms else 0
                building_info = {
                    "id": building.id,
                    "name": building.name,
                    "room_count": room_count,
                    "created_at": building.created_at.strftime('%B %d, %Y') if building.created_at else 'Unknown'
                }
                buildings_data.append(building_info)
        except Exception as e:
            print(f"Database error: {e}")
            # Fallback data for demonstration
            buildings_data = [
                {"id": 1, "name": "Obion County Central High School", "room_count": 25, "created_at": "January 1, 2024"},
                {"id": 2, "name": "Elementary School", "room_count": 15, "created_at": "January 2, 2024"},
                {"id": 3, "name": "Middle School", "room_count": 20, "created_at": "January 3, 2024"},
            ]
        
        return await render_template("buildings.html", {"request": request, "buildings": buildings_data})

    @app.get("/users/add")
    async def add_user_form(request: Request):
        print("📍 /users/add route accessed")
        return await render_template("add_user.html", {"request": request})

    @app.post("/users/add")
    def add_user_submit(request: Request, name: str = Form(...), email: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
        """Add new user to database"""
        print("📍 /users/add submit route accessed")
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
            print(f"✅ User added: {name} ({email})")
        except Exception as e:
            print(f"Error adding user: {e}")
            db.rollback()
        
        return RedirectResponse("/users/list", status_code=303)

    @app.get("/buildings/add")
    async def add_building_form(request: Request):
        print("📍 /buildings/add route accessed")
        return await render_template("add_building.html", {"request": request})

    @app.post("/buildings/add")
    def add_building_submit(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
        """Add new building to database"""
        print("📍 /buildings/add submit route accessed")
        try:
            new_building = Building(name=name)
            db.add(new_building)
            db.commit()
            print(f"✅ Building added: {name}")
        except Exception as e:
            print(f"Error adding building: {e}")
            db.rollback()
        
        return RedirectResponse("/buildings/list", status_code=303)

    @app.get("/buildings/{building_id}/rooms")
    async def building_rooms(request: Request, building_id: int, db: Session = Depends(get_db)):
        """List all rooms in a specific building"""
        print(f"📍 /buildings/{building_id}/rooms route accessed")
        try:
            building = db.query(Building).filter(Building.id == building_id).first()
            if building:
                rooms = db.query(Room).filter(Room.building_id == building_id).order_by(Room.name).all()
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
        
        return await render_template("building_rooms.html", {
            "request": request, 
            "building": building_data, 
            "rooms": rooms_data
        })

    @app.post("/buildings/{building_id}/rooms/add")
    def add_room_submit(request: Request, building_id: int, room_name: str = Form(...), db: Session = Depends(get_db)):
        """Add new room to building"""
        print(f"📍 /buildings/{building_id}/rooms/add submit route accessed")
        try:
            new_room = Room(name=room_name, building_id=building_id)
            db.add(new_room)
            db.commit()
            print(f"✅ Room added: {room_name} to building ID {building_id}")
        except Exception as e:
            print(f"Error adding room: {e}")
            db.rollback()
        
        return RedirectResponse(f"/buildings/{building_id}/rooms", status_code=303)
    
    @app.post("/buildings/{building_id}/rooms/delete/{room_id}")
    def delete_room(request: Request, building_id: int, room_id: int, db: Session = Depends(get_db)):
        """Delete room from building"""
        print(f"📍 /buildings/{building_id}/rooms/delete/{room_id} route accessed")
        try:
            room = db.query(Room).filter(Room.id == room_id, Room.building_id == building_id).first()
            if room:
                db.delete(room)
                db.commit()
                print(f"✅ Room deleted: ID {room_id} from building ID {building_id}")
        except Exception as e:
            print(f"Error deleting room: {e}")
            db.rollback()
        
        return RedirectResponse(f"/buildings/{building_id}/rooms", status_code=303)
    
    # API endpoints for buildings
    @app.get("/api/buildings")
    def get_buildings_api(db: Session = Depends(get_db)):
        """API endpoint to get all buildings"""
        print("📡 /api/buildings route accessed")
        try:
            buildings = db.query(Building).order_by(Building.name).all()
            buildings_data = [
                {
                    "id": building.id,
                    "name": building.name
                }
                for building in buildings
            ]
            return {"buildings": buildings_data}
        except Exception as e:
            print(f"Error fetching buildings: {e}")
            return {"buildings": []}

    @app.get("/api/buildings/{building_id}/rooms")
    def get_building_rooms_api(building_id: int, db: Session = Depends(get_db)):
        """API endpoint to get rooms for a specific building"""
        print(f"📡 /api/buildings/{building_id}/rooms route accessed")
        try:
            rooms = db.query(Room).filter(Room.building_id == building_id).order_by(Room.name).all()
            rooms_data = [
                {
                    "id": room.id,
                    "name": room.name
                }
                for room in rooms
            ]
            return {"rooms": rooms_data}
        except Exception as e:
            print(f"Error fetching building rooms: {e}")
            return {"rooms": []}

    print("✅ User and building routes registered successfully")
