"""
Audit logging service for OCS Portal
"""
from sqlalchemy.orm import Session
from ocs_shared_models import AuditLog
from ocs_shared_models.timezone_utils import central_now
from fastapi import Request
from typing import Optional, Dict, Any
import json

class AuditService:
    """Service for logging user actions and system events"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        user_id: str,
        action_type: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """
        Log a user action to the audit trail
        
        Args:
            user_id: Azure AD User ID
            action_type: Type of action (create, read, update, delete, login, logout, etc.)
            resource_type: Type of resource affected (ticket, inventory, user, etc.)
            resource_id: ID of the affected resource (optional)
            details: Additional details about the action (optional)
            request: FastAPI request object for IP/user agent extraction (optional)
        """
        try:
            # Extract request information if available
            ip_address = None
            user_agent = None
            
            if request:
                # Try to get real IP address from headers (for reverse proxy setups)
                ip_address = (
                    request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                    request.headers.get("X-Real-IP") or
                    getattr(request.client, "host", None)
                )
                user_agent = request.headers.get("User-Agent")
            
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=central_now()
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            # Don't let audit logging failures break the application
            print(f"Audit logging failed: {str(e)}")
            self.db.rollback()
    
    def log_login(self, user_id: str, email: str, access_level: str, request: Optional[Request] = None):
        """Log user login event"""
        self.log_action(
            user_id=user_id,
            action_type="login",
            resource_type="authentication",
            details={
                "email": email,
                "access_level": access_level,
                "login_time": central_now().isoformat()
            },
            request=request
        )
    
    def log_logout(self, user_id: str, email: str, request: Optional[Request] = None):
        """Log user logout event"""
        self.log_action(
            user_id=user_id,
            action_type="logout",
            resource_type="authentication",
            details={
                "email": email,
                "logout_time": central_now().isoformat()
            },
            request=request
        )
    
    def log_ticket_action(
        self, 
        user_id: str, 
        action_type: str, 
        ticket_type: str, 
        ticket_id: str, 
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log ticket-related actions"""
        self.log_action(
            user_id=user_id,
            action_type=action_type,
            resource_type=f"{ticket_type}_ticket",
            resource_id=ticket_id,
            details=details,
            request=request
        )
    
    def log_inventory_action(
        self, 
        user_id: str, 
        action_type: str, 
        item_id: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log inventory-related actions"""
        self.log_action(
            user_id=user_id,
            action_type=action_type,
            resource_type="inventory",
            resource_id=item_id,
            details=details,
            request=request
        )
    
    def log_purchasing_action(
        self, 
        user_id: str, 
        action_type: str, 
        requisition_id: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log purchasing/requisition-related actions"""
        self.log_action(
            user_id=user_id,
            action_type=action_type,
            resource_type="purchasing",
            resource_id=requisition_id,
            details=details,
            request=request
        )
    
    def log_admin_action(
        self, 
        user_id: str, 
        action_type: str, 
        target_resource: str,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ):
        """Log administrative actions"""
        self.log_action(
            user_id=user_id,
            action_type=action_type,
            resource_type="admin",
            resource_id=target_resource,
            details=details,
            request=request
        )
    
    def get_user_activity(self, user_id: str, limit: int = 10):
        """Get recent activity for a specific user"""
        try:
            activities = (
                self.db.query(AuditLog)
                .filter(AuditLog.user_id == user_id)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            
            return [
                {
                    "id": activity.id,
                    "action_type": activity.action_type,
                    "resource_type": activity.resource_type,
                    "resource_id": activity.resource_id,
                    "details": activity.details,
                    "timestamp": activity.timestamp.isoformat(),
                    "ip_address": activity.ip_address
                }
                for activity in activities
            ]
        except Exception as e:
            print(f"Error retrieving user activity: {str(e)}")
            return []
    
    def get_system_activity(self, limit: int = 50):
        """Get recent system-wide activity"""
        try:
            activities = (
                self.db.query(AuditLog)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            
            return [
                {
                    "id": activity.id,
                    "user_id": activity.user_id,
                    "action_type": activity.action_type,
                    "resource_type": activity.resource_type,
                    "resource_id": activity.resource_id,
                    "details": activity.details,
                    "timestamp": activity.timestamp.isoformat(),
                    "ip_address": activity.ip_address
                }
                for activity in activities
            ]
        except Exception as e:
            print(f"Error retrieving system activity: {str(e)}")
            return []

def get_audit_service(db: Session) -> AuditService:
    """Dependency function to get audit service instance"""
    return AuditService(db)

# Convenience function for direct logging
def log_user_action(
    db: Session,
    user_id: str,
    action_type: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
):
    """
    Convenience function to log user actions directly
    
    Args:
        db: Database session
        user_id: Azure AD User ID
        action_type: Type of action (create, read, update, delete, etc.)
        resource_type: Type of resource affected (ticket, inventory, user, etc.)
        resource_id: ID of the affected resource (optional)
        details: Additional details about the action (optional)
        request: FastAPI request object for IP/user agent extraction (optional)
    """
    audit_service = AuditService(db)
    audit_service.log_action(
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        request=request
    )
