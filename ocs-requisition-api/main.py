from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from ocs_shared_models import User, Building, Room
from database import get_db, init_database

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Requisition API")

@app.get("/")
def root():
    return {"message": "OCS Requisition API is running."}

@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    return {"status": "healthy", "service": "requisition-api"}
