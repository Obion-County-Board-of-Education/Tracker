#!/usr/bin/env python3
"""
Database initialization script for OCS services.
This script creates sample data for testing and development.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ocs_shared_models import Base, User, Building, Room, UserRole

def create_databases():
    """Create individual databases for each service"""
    databases = [
        "ocs_portal",
        "ocs_tickets", 
        "ocs_inventory",
        "ocs_requisition",
        "ocs_manage"
    ]
    
    # Connect to PostgreSQL server
    admin_url = "postgresql://ocs_user:ocs_pass@localhost:5433/postgres"
    admin_engine = create_engine(admin_url)
    
    with admin_engine.connect() as conn:
        conn.execute(text("COMMIT"))  # Exit any transaction
        for db_name in databases:
            try:
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✓ Created database: {db_name}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"• Database {db_name} already exists")
                else:
                    print(f"✗ Error creating database {db_name}: {e}")

def init_sample_data():
    """Initialize sample data in the portal database"""
    portal_url = "postgresql://ocs_user:ocs_pass@localhost:5433/ocs_portal"
    engine = create_engine(portal_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Created database tables")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Building).first():
            print("• Sample data already exists")
            return
            
        # Create sample buildings
        buildings = [
            Building(name="Obion County Central High School"),
            Building(name="Obion County Elementary School"),
            Building(name="Lake Road Elementary School"),
            Building(name="Transportation Department"),
            Building(name="Central Office"),
        ]
        
        for building in buildings:
            db.add(building)
        db.commit()
        print("✓ Created sample buildings")
        
        # Create sample rooms
        rooms = [
            Room(name="Computer Lab 1", building_id=1),
            Room(name="Computer Lab 2", building_id=1),
            Room(name="Library", building_id=1),
            Room(name="Office", building_id=1),
            Room(name="Classroom 101", building_id=2),
            Room(name="Classroom 102", building_id=2),
            Room(name="Main Office", building_id=2),
            Room(name="Maintenance Shop", building_id=4),
            Room(name="Director's Office", building_id=5),
        ]
        
        for room in rooms:
            db.add(room)
        db.commit()
        print("✓ Created sample rooms")
        
        # Create sample users
        users = [
            User(
                username="admin",
                display_name="System Administrator",
                email="admin@obionschools.com",
                roles="admin"
            ),
            User(
                username="jsmith",
                display_name="John Smith",
                email="jsmith@obionschools.com", 
                roles="technician"
            ),
            User(
                username="mwilson",
                display_name="Mary Wilson",
                email="mwilson@obionschools.com",
                roles="basic"
            ),
        ]
        
        for user in users:
            db.add(user)
        db.commit()
        print("✓ Created sample users")
        
    except Exception as e:
        print(f"✗ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Initializing OCS databases...")
    
    # Wait for PostgreSQL to be ready
    import time
    time.sleep(2)
    
    try:
        create_databases()
        init_sample_data()
        print("✅ Database initialization complete!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
