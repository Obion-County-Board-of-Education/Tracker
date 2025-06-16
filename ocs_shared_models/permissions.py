"""
Shared permission decorators and utilities for OCS microservices
"""
from functools import wraps
from fastapi import HTTPException, Request, Depends
from typing import List, Optional, Union
import jwt
import os

def get_jwt_secret():
    """Get JWT secret from environment"""
    return os.getenv("JWT_SECRET", "your-secret-key")

def decode_jwt_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user_from_token(request: Request) -> dict:
    """Extract user information from JWT token in Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    return decode_jwt_token(token)

def require_permission(
    service: str, 
    access_level: Union[str, List[str]] = "read",
    allow_admin_override: bool = True
):
    """
    Decorator to require specific service permissions
    
    Args:
        service: Service name (tickets, inventory, purchasing, forms)
        access_level: Required access level(s) - can be string or list
        allow_admin_override: Whether admin/super_admin can override permission check
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Try to get from kwargs
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")
            
            try:
                user = get_current_user_from_token(request)
                user_access_level = user.get('access_level', 'student')
                permissions = user.get('permissions', {})
                
                # Check admin override
                if allow_admin_override and user_access_level in ['admin', 'super_admin']:
                    return await func(*args, **kwargs)
                
                # Check service-specific permission
                service_permission = permissions.get(f'{service}_access', 'none')
                
                # Convert access_level to list if it's a string
                required_levels = access_level if isinstance(access_level, list) else [access_level]
                
                # Check if user has required permission level
                permission_hierarchy = ['none', 'read', 'write', 'admin']
                user_level_index = permission_hierarchy.index(service_permission) if service_permission in permission_hierarchy else 0
                
                has_permission = False
                for required_level in required_levels:
                    if required_level in permission_hierarchy:
                        required_index = permission_hierarchy.index(required_level)
                        if user_level_index >= required_index:
                            has_permission = True
                            break
                
                if not has_permission:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Insufficient permissions. Required: {service} service with {access_level} access"
                    )
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Permission check failed: {str(e)}")
        
        return wrapper
    return decorator

def require_access_level(required_level: Union[str, List[str]]):
    """
    Decorator to require specific user access level
    
    Args:
        required_level: Required access level(s) - can be string or list
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")
            
            try:
                user = get_current_user_from_token(request)
                user_access_level = user.get('access_level', 'student')
                
                # Convert required_level to list if it's a string
                required_levels = required_level if isinstance(required_level, list) else [required_level]
                
                if user_access_level not in required_levels:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Insufficient access level. Required: {required_levels}, Current: {user_access_level}"
                    )
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Access level check failed: {str(e)}")
        
        return wrapper
    return decorator

# Convenience decorators for common permission patterns
def require_tickets_read(func):
    """Require read access to tickets service"""
    return require_permission("tickets", "read")(func)

def require_tickets_write(func):
    """Require write access to tickets service"""
    return require_permission("tickets", "write")(func)

def require_inventory_read(func):
    """Require read access to inventory service"""
    return require_permission("inventory", "read")(func)

def require_inventory_write(func):
    """Require write access to inventory service"""
    return require_permission("inventory", "write")(func)

def require_purchasing_read(func):
    """Require read access to purchasing service"""
    return require_permission("purchasing", "read")(func)

def require_purchasing_write(func):
    """Require write access to purchasing service"""
    return require_permission("purchasing", "write")(func)

def require_forms_read(func):
    """Require read access to forms service"""
    return require_permission("forms", "read")(func)

def require_forms_write(func):
    """Require write access to forms service"""
    return require_permission("forms", "write")(func)

def require_admin(func):
    """Require admin or super_admin access level"""
    return require_access_level(["admin", "super_admin"])(func)

def require_super_admin(func):
    """Require super_admin access level"""
    return require_access_level("super_admin")(func)
