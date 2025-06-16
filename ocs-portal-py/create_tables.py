"""
Create database tables for the authentication system
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ocs_shared_models'))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from models import Base

def create_tables():
    """Create all database tables"""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ocs_user:ocs_pass@localhost:5433/ocs_portal")
        
        engine = create_engine(
            DATABASE_URL,
            connect_args={"connect_timeout": 5},
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        print("🔄 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Created tables ({len(tables)} total):")
        for table in sorted(tables):
            print(f"  - {table}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")

if __name__ == "__main__":
    create_tables()
