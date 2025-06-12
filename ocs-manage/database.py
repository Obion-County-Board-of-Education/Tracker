import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ocs_shared_models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ocs_user:ocs_pass@db:5432/ocs_manage")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database tables - only manage-specific and reference data"""
    # Create tables for manage-specific models and shared reference data
    Base.metadata.create_all(bind=engine)
    print("✓ OCS Manage database tables initialized")
