#!/usr/bin/env python3
"""
Database initialization script for OCS Portal
This script runs on container startup to ensure all required data structures exist
"""
import asyncio
import logging
from sqlalchemy import inspect
from database import engine, SessionLocal
from ocs_shared_models.models import Base, GroupRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create all database tables if they don't exist"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        return False

def setup_group_roles():
    """Set up the proper group role mappings"""
    session = SessionLocal()
    
    try:
        # Check if group roles already exist
        existing_roles = session.query(GroupRole).count()
        if existing_roles > 0:
            logger.info(f"✅ Group roles already exist ({existing_roles} roles found)")
            return True
            
        logger.info("Setting up group role mappings...")
        
        # Define proper group roles based on auth.md
        group_roles = [
            # All Staff - Limited access to tickets and purchasing only
            {
                'group_name': 'All_Staff',
                'azure_group_id': None,
                'access_level': 'staff',
                'tickets_access': 'write',
                'inventory_access': 'none',
                'purchasing_access': 'write',
                'forms_access': 'none',
                'allowed_departments': []
            },
            
            # All Students - Very limited access, tickets only
            {
                'group_name': 'All_Students', 
                'azure_group_id': None,
                'access_level': 'student',
                'tickets_access': 'write',
                'inventory_access': 'none',
                'purchasing_access': 'none',
                'forms_access': 'none',
                'allowed_departments': []
            },
            
            # Technology Department - Full admin access
            {
                'group_name': 'Technology Department',
                'azure_group_id': None,
                'access_level': 'super_admin',
                'tickets_access': 'admin',
                'inventory_access': 'admin',
                'purchasing_access': 'admin',
                'forms_access': 'admin',
                'allowed_departments': ['Technology']
            },
            
            # Finance - Admin access to purchasing, tickets, and forms
            {
                'group_name': 'Finance',
                'azure_group_id': None,
                'access_level': 'admin',
                'tickets_access': 'read',
                'inventory_access': 'read',
                'purchasing_access': 'admin',
                'forms_access': 'admin',
                'allowed_departments': ['Finance']
            }
        ]
        
        # Special role for Director of Schools (via extensionAttribute10)
        director_role = GroupRole(
            group_name='Director of Schools',
            azure_group_id=None,
            azure_user_attribute='extensionAttribute10',
            azure_user_attribute_value='Director of Schools',
            access_level='super_admin',
            tickets_access='admin',
            inventory_access='admin',
            purchasing_access='admin',
            forms_access='admin',
            allowed_departments=['Administration']
        )
        
        # Add all group roles
        for role_data in group_roles:
            role = GroupRole(**role_data)
            session.add(role)
        
        # Add director role
        session.add(director_role)
        
        # Commit changes
        session.commit()
        
        logger.info("✅ Group roles setup complete!")
        
        # Log configured roles
        roles = session.query(GroupRole).all()
        for role in roles:
            logger.info(f"  - {role.group_name}: {role.access_level} access")
            
        return True
            
    except Exception as e:
        logger.error(f"❌ Error setting up group roles: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def wait_for_database():
    """Wait for database to be ready"""
    import time
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Try to connect to the database
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            logger.info("✅ Database connection successful")
            return True
        except Exception as e:
            retry_count += 1
            logger.info(f"Waiting for database... (attempt {retry_count}/{max_retries})")
            time.sleep(2)
    
    logger.error("❌ Failed to connect to database after maximum retries")
    return False

def initialize_database():
    """Main initialization function"""
    logger.info("🚀 Starting database initialization...")
    
    # Wait for database to be ready
    if not wait_for_database():
        return False
    
    # Create tables
    if not create_tables():
        return False
    
    # Setup group roles
    if not setup_group_roles():
        return False
    
    logger.info("✅ Database initialization completed successfully!")
    return True

if __name__ == "__main__":
    success = initialize_database()
    if not success:
        exit(1)
