"""
Authentication and authorization utilities for OCS Tracker.
This module provides shared authentication functionality including:
- JWT token generation and validation
- Session management
- User role resolution
- Permission validation
"""

import os
import jwt
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "development-secret-change-in-production")
JWT_ALGORITHM = "HS256"
SESSION_TIMEOUT_MINUTES = int(os.environ.get("SESSION_TIMEOUT_MINUTES", "30"))
MAX_CONCURRENT_SESSIONS = int(os.environ.get("MAX_CONCURRENT_SESSIONS", "3"))

# Role and permission constants
ACCESS_LEVELS = {
    "super_admin": 4,
    "admin": 3,
    "write": 2,
    "read": 1,
    "none": 0
}

SERVICE_NAMES = [
    "tickets",
    "inventory",
    "purchasing",
    "forms",
    "user_management",
    "reports",
    "system"
]

class AuthError(Exception):
    """Authentication or authorization error"""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def generate_token(user_id: str, email: str, display_name: str, 
                  roles: List[str], expiration_minutes: int = SESSION_TIMEOUT_MINUTES) -> str:
    """
    Generate a JWT token for user authentication
    
    Args:
        user_id: Azure AD user ID or internal user ID
        email: User's email address
        display_name: User's display name
        roles: List of role strings (from Azure AD groups)
        expiration_minutes: Token validity duration in minutes
    
    Returns:
        Encoded JWT token string
    """
    now = int(time.time())
    expiration_time = now + (expiration_minutes * 60)
    
    payload = {
        "sub": user_id,
        "email": email,
        "name": display_name,
        "roles": roles,
        "iat": now,
        "exp": expiration_time,
        "jti": str(uuid.uuid4())  # JWT ID - unique identifier for the token
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate a JWT token and return the payload
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        AuthError: If token is invalid, expired, or malformed
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Authentication expired", 401)
    except jwt.InvalidTokenError:
        raise AuthError("Invalid authentication token", 401)


def get_permission_level(user_roles: List[str], extension_attribute_10: Optional[str] = None) -> Dict[str, int]:
    """
    Calculate permission levels for a user based on their roles
    
    Args:
        user_roles: List of Azure AD group names/IDs
        extension_attribute_10: Value of extensionAttribute10 from Azure AD
    
    Returns:
        Dict mapping service names to permission levels
    """
    # Default to no access for all services
    permissions = {service: ACCESS_LEVELS["none"] for service in SERVICE_NAMES}
    
    # Check for Technology Department (highest access)
    if "Technology Department" in user_roles:
        return {service: ACCESS_LEVELS["super_admin"] for service in SERVICE_NAMES}
    
    # Check for Director of Schools through extensionAttribute10
    if extension_attribute_10 and "Director of Schools" in extension_attribute_10:
        return {service: ACCESS_LEVELS["super_admin"] for service in SERVICE_NAMES}
    
    # Check for Finance group (high access)
    if "Finance" in user_roles:
        return {
            service: ACCESS_LEVELS["super_admin"] for service in SERVICE_NAMES
        }
    
    # Basic staff permissions
    if "All_Staff" in user_roles:
        permissions.update({
            "tickets": ACCESS_LEVELS["write"],       # Create/view own tickets
            "inventory": ACCESS_LEVELS["read"],      # View inventory
            "purchasing": ACCESS_LEVELS["write"],    # Submit/view own requisitions
            "forms": ACCESS_LEVELS["write"]          # Submit forms
        })
    
    # Student permissions (most limited)
    if "All_Students" in user_roles:
        permissions.update({
            "tickets": ACCESS_LEVELS["write"]        # Create/view own tickets only
        })
        
    return permissions


def has_permission(user_permissions: Dict[str, int], service: str, required_level: str) -> bool:
    """
    Check if a user has the required permission level for a service
    
    Args:
        user_permissions: Dict of user permissions from get_permission_level()
        service: Service name to check
        required_level: Required permission level (e.g., "read", "write", "admin")
    
    Returns:
        Boolean indicating if the user has sufficient permission
    """
    if service not in user_permissions:
        return False
    
    required_level_value = ACCESS_LEVELS.get(required_level, 0)
    user_level_value = user_permissions.get(service, 0)
    
    return user_level_value >= required_level_value
