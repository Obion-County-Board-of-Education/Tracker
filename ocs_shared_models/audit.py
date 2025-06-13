"""
Audit logging utilities for OCS Tracker.
This module provides functions for logging user actions for security and compliance.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Optional, Any


def log_audit_event(
    db: Session,
    user_id: str,
    action_type: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
):
    """
    Log an audit event to the database
    
    Args:
        db: Database session
        user_id: ID of the user performing the action
        action_type: Type of action (create, read, update, delete, login, logout, etc.)
        resource_type: Type of resource being acted on (user, ticket, inventory, etc.)
        resource_id: ID of the resource being acted on
        details: Additional details about the action
        ip_address: IP address of the user
    """
    try:
        # Insert audit log entry
        db.execute(
            text("""
            INSERT INTO audit_log 
            (user_id, action_type, resource_type, resource_id, details, ip_address, created_at)
            VALUES 
            (:user_id, :action_type, :resource_type, :resource_id, :details, :ip_address, NOW())
            """),
            {
                "user_id": user_id,
                "action_type": action_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": str(details) if details else None,
                "ip_address": ip_address
            }
        )
        db.commit()
        
    except Exception as e:
        # Log to console but don't fail the operation if audit logging fails
        print(f"Error logging audit event: {str(e)}")
        # Don't rollback the transaction, as this would affect the main operation
        # The main operation should handle its own transactions


def get_audit_logs(
    db: Session, 
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get audit logs with optional filters
    
    Args:
        db: Database session
        user_id: Filter by user ID
        action_type: Filter by action type
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        
    Returns:
        List of audit logs
    """
    # Build query conditions
    conditions = []
    params = {
        "limit": limit,
        "offset": offset
    }
    
    if user_id:
        conditions.append("user_id = :user_id")
        params["user_id"] = user_id
        
    if action_type:
        conditions.append("action_type = :action_type")
        params["action_type"] = action_type
        
    if resource_type:
        conditions.append("resource_type = :resource_type")
        params["resource_type"] = resource_type
        
    if resource_id:
        conditions.append("resource_id = :resource_id")
        params["resource_id"] = resource_id
        
    if start_date:
        conditions.append("created_at >= :start_date")
        params["start_date"] = start_date
        
    if end_date:
        conditions.append("created_at <= :end_date")
        params["end_date"] = end_date
    
    # Build the WHERE clause
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = f"WHERE {where_clause}"
    
    # Execute query
    result = db.execute(
        text(f"""
        SELECT 
            id,
            user_id,
            action_type,
            resource_type,
            resource_id,
            details,
            ip_address,
            created_at
        FROM 
            audit_log
        {where_clause}
        ORDER BY 
            created_at DESC
        LIMIT :limit OFFSET :offset
        """),
        params
    )
    
    # Convert result to list of dictionaries
    logs = []
    for row in result:
        logs.append({
            "id": row.id,
            "user_id": row.user_id,
            "action_type": row.action_type,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "details": row.details,
            "ip_address": row.ip_address,
            "created_at": row.created_at.isoformat() if row.created_at else None
        })
    
    return logs
