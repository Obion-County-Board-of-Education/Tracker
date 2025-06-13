"""
User profile routes for OCS Tracker portal.
Handles displaying and updating user profile information.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Dict, Optional

from ocs_shared_models.database import get_db
from ocs_shared_models.auth_middleware import get_current_user
from ocs_shared_models.timezone_utils import format_central_time

router = APIRouter(tags=["User"])


@router.get("/user/profile", response_class=HTMLResponse)
async def view_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Display the user's profile information
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user info
    
    Returns:
        User profile page HTML
    """
    try:
        # Get session info from database
        result = db.execute(
            text("""
            SELECT 
                last_activity,
                expires_at
            FROM 
                user_sessions
            WHERE 
                user_id = :user_id
            ORDER BY 
                last_activity DESC
            LIMIT 1
            """),
            {"user_id": current_user["id"]}
        )
        
        session_info = result.fetchone()
        
        if session_info:
            last_activity = format_central_time(session_info.last_activity)
            session_expires = format_central_time(session_info.expires_at)
        else:
            last_activity = "Unknown"
            session_expires = "Unknown"
        
        # Render profile template
        from main import templates  # Import here to avoid circular imports
        return templates.TemplateResponse(
            "user_profile.html",
            {
                "request": request,
                "user": current_user,
                "last_activity": last_activity,
                "session_expires": session_expires
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile: {str(e)}")
