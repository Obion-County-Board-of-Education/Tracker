import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ocs_shared_models import Base, SystemMessage, User, Building, Room

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ocs_user:ocs_pass@db:5432/ocs_portal")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
    # Only create tables for portal-specific models and shared reference data
    # Tickets are handled by the Tickets API service
    SystemMessage.metadata.create_all(bind=engine)
    User.metadata.create_all(bind=engine)
    Building.metadata.create_all(bind=engine)
    Room.metadata.create_all(bind=engine)
