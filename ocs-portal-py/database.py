import os
import sys
from pathlib import Path

# Add parent directory to path for shared models access
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# Import shared models with proper fallback handling
try:
    from ocs_shared_models.models import Base, SystemMessage, User, Building, Room
except ImportError:
    try:
        from ocs_shared_models import Base, SystemMessage, User, Building, Room
    except ImportError:
        # Final fallback for development
        sys.path.insert(0, '../ocs_shared_models')
        from models import Base, SystemMessage, User, Building, Room

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ocs_user:ocs_pass@localhost:5433/ocs_portal")

# Create engine with connection timeout and error handling
try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"connect_timeout": 5},
        pool_pre_ping=True,
        pool_recycle=300
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print(f"✅ Database engine created successfully")
except Exception as e:
    print(f"⚠️ Database connection issue: {e}")
    # Create fallback engine
    engine = create_engine("sqlite:///./fallback.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("📁 Using SQLite fallback database")

def get_db() -> Session:
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Initialize database tables and essential data"""
    try:
        # Test database connection first
        with engine.connect() as connection:
            print("✅ Database connection successful")
        
        # Only create tables for portal-specific models and shared reference data
        # Tickets are handled by the Tickets API service
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully")
        
        # Setup essential GroupRole mappings
        setup_essential_group_roles()
        
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("🔄 Application will continue but database features may be limited")

def setup_essential_group_roles():
    """Set up essential group role mappings if they don't exist"""
    from ocs_shared_models.models import GroupRole
    
    try:
        db = SessionLocal()
        
        # Check if group roles already exist
        existing_roles = db.query(GroupRole).count()
        if existing_roles > 0:
            print(f"✅ Group roles already exist ({existing_roles} roles found)")
            return
            
        print("🔧 Setting up essential group role mappings...")
        
        # Define essential group roles
        essential_roles = [
            # All Staff - Limited access to tickets and purchasing only
            GroupRole(
                group_name='All_Staff',
                access_level='staff',
                tickets_access='write',
                inventory_access='none',
                purchasing_access='write',
                forms_access='none',
                allowed_departments=[]
            ),
            
            # All Students - Very limited access, tickets only
            GroupRole(
                group_name='All_Students',
                access_level='student',
                tickets_access='write',
                inventory_access='none',
                purchasing_access='none',
                forms_access='none',
                allowed_departments=[]
            ),
            
            # Technology Department - Full admin access
            GroupRole(
                group_name='Technology Department',
                access_level='super_admin',
                tickets_access='admin',
                inventory_access='admin',
                purchasing_access='admin',
                forms_access='admin',
                allowed_departments=['Technology']
            ),
            
            # Finance - Admin access to purchasing, tickets, and forms
            GroupRole(
                group_name='Finance',
                access_level='admin',
                tickets_access='read',
                inventory_access='read',
                purchasing_access='admin',
                forms_access='admin',
                allowed_departments=['Finance']
            ),
            
            # Special role for Director of Schools (via extensionAttribute10)
            GroupRole(
                group_name='Director of Schools',
                azure_user_attribute='extensionAttribute10',
                azure_user_attribute_value='Director of Schools',
                access_level='super_admin',
                tickets_access='admin',
                inventory_access='admin',
                purchasing_access='admin',
                forms_access='admin',
                allowed_departments=['Administration']
            )
        ]
        
        # Add all essential roles
        for role in essential_roles:
            db.add(role)
        
        # Commit changes
        db.commit()
        
        print("✅ Essential group roles setup complete!")
        print("   - All_Staff: staff access")
        print("   - All_Students: student access") 
        print("   - Technology Department: super_admin access")
        print("   - Finance: admin access")
        print("   - Director of Schools: super_admin access (via extensionAttribute10)")
            
    except Exception as e:
        print(f"⚠️ Error setting up group roles: {e}")
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()
