"""
Health check endpoint for the portal service
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    """Health check endpoint for container healthchecks"""
    return {"status": "healthy", "service": "portal-py"}
