"""
Dashboard routes for OCS Tracker portal.
Handles displaying personalized dashboard based on user roles and permissions.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

from ocs_shared_models.database import get_db
from ocs_shared_models.auth_middleware import get_current_user
from ocs_shared_models.timezone_utils import format_central_time

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def view_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Display the user's personalized dashboard
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user info
    
    Returns:
        Dashboard page HTML
    """
    try:
        user_id = current_user["id"]
        user_permissions = current_user.get("permissions", {})
        
        # Get user's last login
        result = db.execute(
            text("""
            SELECT 
                last_activity 
            FROM 
                user_sessions 
            WHERE 
                user_id = :user_id 
            ORDER BY 
                last_activity DESC 
            OFFSET 1 
            LIMIT 1
            """),
            {"user_id": user_id}
        )
        
        session_info = result.fetchone()
        last_login = format_central_time(session_info.last_activity) if session_info else "First login"
        
        # Get system messages
        result = db.execute(text("SELECT * FROM system_messages WHERE active = TRUE ORDER BY created_at DESC LIMIT 5"))
        system_messages = []
        
        for row in result:
            system_messages.append({
                "title": row.title,
                "content": row.message,
                "level": row.level,
                "timestamp": format_central_time(row.created_at) if row.created_at else None
            })
        
        # Get ticket statistics if user has ticket permissions
        ticket_stats = None
        if user_permissions.get("tickets", 0) > 0:
            result = db.execute(
                text("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'open') AS open,
                    COUNT(*) FILTER (WHERE status = 'assigned') AS assigned,
                    COUNT(*) FILTER (WHERE status = 'closed') AS closed,
                    COUNT(*) AS total
                FROM
                    tickets
                WHERE
                    created_by = :user_id
                    OR assigned_to = :user_id
                    OR :is_admin = TRUE
                """),
                {
                    "user_id": user_id,
                    "is_admin": user_permissions.get("tickets", 0) >= 3
                }
            )
            
            row = result.fetchone()
            if row:
                ticket_stats = {
                    "open": row.open,
                    "assigned": row.assigned,
                    "closed": row.closed,
                    "total": row.total
                }
        
        # Get inventory statistics if user has inventory permissions
        inventory_stats = None
        if user_permissions.get("inventory", 0) > 0:
            result = db.execute(
                text("""
                SELECT
                    COUNT(DISTINCT id) AS total,
                    COUNT(DISTINCT category) AS categories
                FROM
                    inventory
                """)
            )
            
            row = result.fetchone()
            if row:
                inventory_stats = {
                    "total": row.total,
                    "categories": row.categories
                }
        
        # Get requisition statistics if user has purchasing permissions
        requisition_stats = None
        if user_permissions.get("purchasing", 0) > 0:
            result = db.execute(
                text("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'submitted') AS submitted,
                    COUNT(*) FILTER (WHERE status = 'approved') AS approved,
                    COUNT(*) FILTER (WHERE status = 'rejected') AS rejected,
                    COUNT(*) FILTER (WHERE status = 'pending_approval') AS pending_approval
                FROM
                    requisitions
                WHERE
                    created_by = :user_id
                    OR approver = :user_id
                    OR :is_admin = TRUE
                """),
                {
                    "user_id": user_id,
                    "is_admin": user_permissions.get("purchasing", 0) >= 3
                }
            )
            
            row = result.fetchone()
            if row:
                requisition_stats = {
                    "submitted": row.submitted,
                    "approved": row.approved,
                    "rejected": row.rejected,
                    "pending_approval": row.pending_approval
                }
        
        # Render dashboard template
        from main import templates  # Import here to avoid circular imports
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user,
                "user_permissions": user_permissions,
                "last_login": last_login,
                "system_messages": system_messages,
                "ticket_stats": ticket_stats,
                "inventory_stats": inventory_stats,
                "requisition_stats": requisition_stats
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dashboard: {str(e)}")
