import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ocs_shared_models import Base, Building

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ocs_user:ocs_pass@db:5432/ocs_sheets")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_sample_buildings():
    """Initialize sample buildings if they don't exist"""
    db = SessionLocal()
    try:
        # Check if buildings already exist
        if db.query(Building).first():
            return
            
        # Create sample buildings
        buildings = [
            Building(name="Main Building"),
            Building(name="Annex Building"), 
            Building(name="Gymnasium"),
            Building(name="Library"),
            Building(name="Cafeteria"),
            Building(name="Outdoor Area"),
        ]
        
        for building in buildings:
            db.add(building)
        db.commit()
        print("✓ Created sample buildings in sheets database")
        
    except Exception as e:
        print(f"Error creating sample buildings: {e}")
        db.rollback()
    finally:
        db.close()

# Create tables
def init_database():
    """Initialize database tables and sample data"""
    Base.metadata.create_all(bind=engine)
    init_sample_buildings()
