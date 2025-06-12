import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from ocs_shared_models import User, Building, Room
from database import get_db, init_database

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Inventory API")

@app.get("/")
def root():
    return {"message": "OCS Inventory API is running."}

@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    return {"status": "healthy", "service": "inventory-api"}
