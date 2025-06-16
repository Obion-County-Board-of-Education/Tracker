import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
<<<<<<< HEAD

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ocs_shared_models import Base, SystemMessage, User, Building, Room

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ocs_user:ocs_pass@db:5432/ocs_portal")
=======
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
try:
    from ocs_shared_models import Base, SystemMessage, User, Building, Room
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, '../ocs_shared_models')
    from models import Base, SystemMessage, User, Building, Room

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ocs_user:ocs_pass@localhost:5433/ocs_portal")
>>>>>>> 2fd8c62 (add auth with graph)

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
    # Fallback for development without database
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///./fallback.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("📁 Using SQLite fallback database")

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables only for portal-specific models and shared reference data
def init_database():
    """Initialize database tables - only portal-specific and reference data"""
    try:
        # Test database connection first
        with engine.connect() as connection:
            print("✅ Database connection successful")
        
        # Only create tables for portal-specific models and shared reference data
        # Tickets are handled by the Tickets API service
        SystemMessage.metadata.create_all(bind=engine)
        User.metadata.create_all(bind=engine)
        Building.metadata.create_all(bind=engine)
        Room.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully")
        
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("🔄 Application will continue but database features may be limited")
