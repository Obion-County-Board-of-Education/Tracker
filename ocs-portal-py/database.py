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
    """Initialize database tables - only portal-specific and reference data"""
    try:
        # Test database connection first
        with engine.connect() as connection:
            print("✅ Database connection successful")
        
        # Only create tables for portal-specific models and shared reference data
        # Tickets are handled by the Tickets API service
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully")
        
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("🔄 Application will continue but database features may be limited")
