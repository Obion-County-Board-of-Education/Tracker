#!/usr/bin/env python3
"""
Development Database Setup Script
Creates consistent test data for all developers
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'ocs-portal-py'))

from datetime import datetime, timedelta
from database import get_db, init_database
from ocs_shared_models import Building, Room, TechTicket, MaintenanceTicket

def setup_dev_database():
    """Set up development database with sample data"""
    print("🔧 Setting up development database...")
    
    try:
        # Initialize database
        init_database()
        db = next(get_db())
        
        # Clear existing data
        print("🗑️ Clearing existing data...")
        db.query(TechTicket).delete()
        db.query(MaintenanceTicket).delete()
        db.query(Room).delete()
        db.query(Building).delete()
        
        # Create sample buildings
        print("🏢 Creating sample buildings...")
        buildings_data = [
            {"id": 1, "name": "Main Building"},
            {"id": 2, "name": "Elementary School"},
            {"id": 3, "name": "High School"},
            {"id": 4, "name": "Middle School"},
            {"id": 5, "name": "Administration"}
        ]
        
        for building_data in buildings_data:
            building = Building(**building_data)
            db.add(building)
        
        # Create sample rooms
        print("🚪 Creating sample rooms...")
        rooms_data = [
            # Main Building
            {"id": 1, "name": "Room 101", "building_id": 1},
            {"id": 2, "name": "Room 102", "building_id": 1},
            {"id": 3, "name": "Computer Lab", "building_id": 1},
            {"id": 4, "name": "Library", "building_id": 1},
            
            # Elementary School
            {"id": 5, "name": "Classroom A", "building_id": 2},
            {"id": 6, "name": "Classroom B", "building_id": 2},
            {"id": 7, "name": "Cafeteria", "building_id": 2},
            
            # High School
            {"id": 8, "name": "Science Lab", "building_id": 3},
            {"id": 9, "name": "Gymnasium", "building_id": 3},
            {"id": 10, "name": "Auditorium", "building_id": 3},
        ]
        
        for room_data in rooms_data:
            room = Room(**room_data)
            db.add(room)
        
        # Create sample tech tickets
        print("💻 Creating sample tech tickets...")
        tech_tickets = [
            {
                "title": "Computer won't start",
                "description": "Desktop computer in Room 101 won't boot up",
                "school": "Main Building",
                "room": "Room 101",
                "issue_type": "hardware",
                "status": "open",
                "created_by": "John Doe",
                "created_at": datetime.now() - timedelta(days=2)
            },
            {
                "title": "Projector display issue",
                "description": "Projector in Science Lab showing blurry images",
                "school": "High School",
                "room": "Science Lab",
                "issue_type": "hardware",
                "status": "assigned",
                "created_by": "Jane Smith",
                "created_at": datetime.now() - timedelta(days=1)
            },
            {
                "title": "WiFi connectivity problems",
                "description": "Students unable to connect to school WiFi",
                "school": "Elementary School",
                "room": "Classroom A",
                "issue_type": "network",
                "status": "closed",
                "created_by": "Bob Johnson",
                "created_at": datetime.now() - timedelta(days=5)
            },
            {
                "title": "Software installation request",
                "description": "Need to install Adobe Creative Suite",
                "school": "Main Building",
                "room": "Computer Lab",
                "issue_type": "software",
                "status": "new",
                "created_by": "Alice Brown",
                "created_at": datetime.now()
            }
        ]
        
        for ticket_data in tech_tickets:
            ticket = TechTicket(**ticket_data)
            db.add(ticket)
        
        # Create sample maintenance tickets
        print("🔧 Creating sample maintenance tickets...")
        maintenance_tickets = [
            {
                "title": "Air conditioning not working",
                "description": "AC unit in cafeteria not cooling properly",
                "school": "Elementary School",
                "room": "Cafeteria",
                "issue_type": "hvac",
                "status": "open",
                "created_by": "Mike Wilson",
                "created_at": datetime.now() - timedelta(days=1)
            },
            {
                "title": "Leaky faucet in restroom",
                "description": "Faucet in main restroom dripping constantly",
                "school": "Main Building",
                "room": "Restroom",
                "issue_type": "plumbing",
                "status": "assigned",
                "created_by": "Sarah Davis",
                "created_at": datetime.now() - timedelta(days=3)
            },
            {
                "title": "Broken window",
                "description": "Window in gymnasium has a crack",
                "school": "High School",
                "room": "Gymnasium",
                "issue_type": "structural",
                "status": "closed",
                "created_by": "Tom Anderson",
                "created_at": datetime.now() - timedelta(days=7)
            }
        ]
        
        for ticket_data in maintenance_tickets:
            ticket = MaintenanceTicket(**ticket_data)
            db.add(ticket)
        
        # Commit all changes
        db.commit()
        print("✅ Development database setup complete!")
        print(f"📊 Created:")
        print(f"   - {len(buildings_data)} buildings")
        print(f"   - {len(rooms_data)} rooms")
        print(f"   - {len(tech_tickets)} tech tickets")
        print(f"   - {len(maintenance_tickets)} maintenance tickets")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_dev_database()
