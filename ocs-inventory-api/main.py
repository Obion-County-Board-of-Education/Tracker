from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from ocs_shared_models import User, Building, Room
from database import get_db, init_database
from auth_middleware import AuthMiddleware, get_current_user, has_permission

# Initialize database on startup
init_database()

app = FastAPI(title="OCS Inventory API")

# Add authentication middleware with excluded paths
app.add_middleware(
    AuthMiddleware,
    exclude_paths=[
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc"
    ]
)

@app.get("/")
def root():
    return {"message": "OCS Inventory API is running."}

@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring"""
    return {"status": "healthy", "service": "inventory-api"}
