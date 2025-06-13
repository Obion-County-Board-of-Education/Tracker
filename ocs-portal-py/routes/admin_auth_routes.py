"""
Admin routes for authentication management.
These routes allow administrators to manage user roles and permissions.
"""

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime
from typing import List, Dict, Optional

from ocs_shared_models.database import get_db
from ocs_shared_models.auth import AuthError
from ocs_shared_models.auth_middleware import get_current_user, require_permission

router = APIRouter(prefix="/admin/auth", tags=["Admin", "Authentication"])


@router.get("/roles")
@require_permission("user_management", "admin")
async def list_roles(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    List all role definitions
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user info
    
    Returns:
        List of role definitions
    """
    try:
        result = db.execute(text("SELECT * FROM group_roles ORDER BY group_name"))
        roles = []
        
        for row in result:
            roles.append({
                "id": row.id,
                "azure_group_id": row.azure_group_id,
                "group_name": row.group_name,
                "access_level": row.access_level,
                "tickets_access": row.tickets_access,
                "inventory_access": row.inventory_access,
                "purchasing_access": row.purchasing_access,
                "forms_access": row.forms_access,
                "allowed_departments": json.loads(row.allowed_departments) if row.allowed_departments else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            })
        
        return {"roles": roles}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve roles: {str(e)}")


@router.post("/roles")
@require_permission("user_management", "admin")
async def create_role(
    request: Request,
    role: Dict,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new role definition
    
    Args:
        request: FastAPI request object
        role: Role definition
        db: Database session
        current_user: Current authenticated user info
    
    Returns:
        Created role definition
    """
    required_fields = ["azure_group_id", "group_name", "access_level"]
    for field in required_fields:
        if field not in role:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    try:
        # Convert allowed_departments to JSON string if present
        allowed_departments = json.dumps(role.get("allowed_departments")) if role.get("allowed_departments") else None
        
        # Use parameterized query to prevent SQL injection
        result = db.execute(
            text("""
            INSERT INTO group_roles 
            (azure_group_id, group_name, access_level, tickets_access, inventory_access, 
             purchasing_access, forms_access, allowed_departments)
            VALUES 
            (:azure_group_id, :group_name, :access_level, :tickets_access, :inventory_access,
             :purchasing_access, :forms_access, :allowed_departments)
            RETURNING id
            """),
            {
                "azure_group_id": role["azure_group_id"],
                "group_name": role["group_name"],
                "access_level": role["access_level"],
                "tickets_access": role.get("tickets_access", "none"),
                "inventory_access": role.get("inventory_access", "none"),
                "purchasing_access": role.get("purchasing_access", "none"),
                "forms_access": role.get("forms_access", "none"),
                "allowed_departments": allowed_departments
            }
        )
        
        db.commit()
        role_id = result.fetchone()[0]
        
        # Log the action
        db.execute(
            text("""
            INSERT INTO audit_log 
            (user_id, action_type, resource_type, resource_id, details, ip_address)
            VALUES 
            (:user_id, 'create', 'role', :role_id, :details, :ip_address)
            """),
            {
                "user_id": current_user["id"],
                "role_id": str(role_id),
                "details": json.dumps(role),
                "ip_address": request.client.host
            }
        )
        db.commit()
        
        return {"id": role_id, **role}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create role: {str(e)}")


@router.put("/roles/{role_id}")
@require_permission("user_management", "admin")
async def update_role(
    role_id: int,
    role: Dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Update an existing role definition
    
    Args:
        role_id: Role ID to update
        role: Updated role definition
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user info
    
    Returns:
        Updated role definition
    """
    try:
        # Convert allowed_departments to JSON string if present
        allowed_departments = json.dumps(role.get("allowed_departments")) if role.get("allowed_departments") else None
        
        # Use parameterized query to prevent SQL injection
        result = db.execute(
            text("""
            UPDATE group_roles SET
                group_name = :group_name,
                access_level = :access_level,
                tickets_access = :tickets_access,
                inventory_access = :inventory_access,
                purchasing_access = :purchasing_access,
                forms_access = :forms_access,
                allowed_departments = :allowed_departments,
                updated_at = NOW()
            WHERE id = :role_id
            RETURNING id
            """),
            {
                "role_id": role_id,
                "group_name": role["group_name"],
                "access_level": role["access_level"],
                "tickets_access": role.get("tickets_access", "none"),
                "inventory_access": role.get("inventory_access", "none"),
                "purchasing_access": role.get("purchasing_access", "none"),
                "forms_access": role.get("forms_access", "none"),
                "allowed_departments": allowed_departments
            }
        )
        
        if not result.rowcount:
            raise HTTPException(status_code=404, detail=f"Role with ID {role_id} not found")
            
        db.commit()
        
        # Log the action
        db.execute(
            text("""
            INSERT INTO audit_log 
            (user_id, action_type, resource_type, resource_id, details, ip_address)
            VALUES 
            (:user_id, 'update', 'role', :role_id, :details, :ip_address)
            """),
            {
                "user_id": current_user["id"],
                "role_id": str(role_id),
                "details": json.dumps(role),
                "ip_address": request.client.host
            }
        )
        db.commit()
        
        return {"id": role_id, **role}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update role: {str(e)}")


@router.get("/sessions")
@require_permission("user_management", "admin")
async def list_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    List active user sessions
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user info
        limit: Maximum number of sessions to return
        offset: Pagination offset
    
    Returns:
        List of active sessions
    """
    try:
        # Get total count
        count_result = db.execute(text("SELECT COUNT(*) FROM user_sessions WHERE expires_at > NOW()"))
        total = count_result.scalar()
        
        # Get sessions with pagination
        result = db.execute(
            text("""
            SELECT * FROM user_sessions
            WHERE expires_at > NOW()
            ORDER BY last_activity DESC
            LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset}
        )
        
        sessions = []
        for row in result:
            sessions.append({
                "id": row.id,
                "user_id": row.user_id,
                "email": row.email,
                "display_name": row.display_name,
                "access_level": row.access_level,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "last_activity": row.last_activity.isoformat() if row.last_activity else None,
                "expires_at": row.expires_at.isoformat() if row.expires_at else None
            })
        
        return {
            "sessions": sessions,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sessions: {str(e)}")


@router.delete("/sessions/{session_id}")
@require_permission("user_management", "admin")
async def revoke_session(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Revoke a specific user session
    
    Args:
        session_id: Session ID to revoke
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user info
    
    Returns:
        Success message
    """
    try:
        result = db.execute(
            text("DELETE FROM user_sessions WHERE id = :session_id"),
            {"session_id": session_id}
        )
        
        if not result.rowcount:
            raise HTTPException(status_code=404, detail=f"Session with ID {session_id} not found")
            
        db.commit()
        
        # Log the action
        db.execute(
            text("""
            INSERT INTO audit_log 
            (user_id, action_type, resource_type, resource_id, ip_address)
            VALUES 
            (:user_id, 'revoke', 'session', :session_id, :ip_address)
            """),
            {
                "user_id": current_user["id"],
                "session_id": str(session_id),
                "ip_address": request.client.host
            }
        )
        db.commit()
        
        return {"message": f"Session {session_id} has been revoked"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to revoke session: {str(e)}")


@router.get("/audit")
@require_permission("user_management", "admin")
async def get_audit_logs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """
    Get security audit logs with filtering options
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user
        limit: Maximum number of logs to return
        offset: Pagination offset
        action_type: Filter by action type (e.g., "login", "create", "update")
        resource_type: Filter by resource type (e.g., "role", "session")
        user_id: Filter by user ID
        from_date: Filter by date range start (ISO format)
        to_date: Filter by date range end (ISO format)
    
    Returns:
        List of audit logs
    """
    try:
        # Build WHERE clause based on filters
        where_clauses = []
        params = {"limit": limit, "offset": offset}
        
        if action_type:
            where_clauses.append("action_type = :action_type")
            params["action_type"] = action_type
            
        if resource_type:
            where_clauses.append("resource_type = :resource_type")
            params["resource_type"] = resource_type
            
        if user_id:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
            
        if from_date:
            where_clauses.append("timestamp >= :from_date")
            params["from_date"] = from_date
            
        if to_date:
            where_clauses.append("timestamp <= :to_date")
            params["to_date"] = to_date
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        count_result = db.execute(
            text(f"SELECT COUNT(*) FROM audit_log WHERE {where_clause}"),
            params
        )
        total = count_result.scalar()
        
        # Get audit logs with pagination
        query = f"""
        SELECT * FROM audit_log
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
        """
        
        result = db.execute(text(query), params)
        
        logs = []
        for row in result:
            logs.append({
                "id": row.id,
                "user_id": row.user_id,
                "action_type": row.action_type,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "details": json.loads(row.details) if row.details else None,
                "ip_address": row.ip_address,
                "user_agent": row.user_agent,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None
            })
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit logs: {str(e)}")
