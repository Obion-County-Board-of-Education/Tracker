import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ocs_shared_models')))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ocs_shared_models.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ocs_user:ocs_pass@db:5432/ocs_portal")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables for all shared models in the portal database
Base.metadata.create_all(bind=engine)
