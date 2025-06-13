"""
Authentication middleware for FastAPI applications in OCS Tracker.
This middleware handles authentication and authorization for all API requests.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Callable, Union
import functools
import json
import logging
from datetime import datetime, timedelta

from .database import get_db
from .auth import validate_token, AuthError, has_permission

# Setup logging
logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# Authentication paths that should bypass the auth middleware
PUBLIC_PATHS = [
    "/auth/login",
    "/auth/callback",
    "/auth/status",
    "/static",
    "/docs",
    "/openapi.json",
    "/redoc",
]

class AuthMiddleware:
    """
    Authentication middleware for FastAPI
    Validates JWT tokens and enforces permission-based access control
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        """
        Process each request through the authentication middleware
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or route handler
        
        Returns:
            Response from next handler or error response
        """
        # Check if path should bypass authentication
        path = request.url.path
        if any(path.startswith(public) for public in PUBLIC_PATHS):
            return await call_next(request)
        
        # Get token from cookie or authorization header
        token = request.cookies.get("ocs_session")
        
        if not token:
            # Try Authorization header as fallback
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split("Bearer ")[1]
        
        if not token:
            # No valid token found, redirect to login
            original_url = str(request.url)
            login_url = f"/auth/login?redirect_url={original_url}"
            return RedirectResponse(url=login_url, status_code=302)
            
        try:
            # Validate token
            payload = validate_token(token)
            
            # Add user info to request state
            request.state.user = {
                "id": payload["sub"],
                "email": payload["email"],
                "name": payload["name"],
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", {}),
            }
            
            # Update session in database if using database sessions
            try:
                db = next(get_db())
                session_record = db.execute(
                    """
                    UPDATE user_sessions 
                    SET last_activity = NOW(), 
                        expires_at = NOW() + INTERVAL '%s minutes'
                    WHERE token = %s
                    """, 
                    (30, token)
                )
                db.commit()
            except Exception as e:
                logger.warning(f"Failed to update session: {e}")
            
            # Continue to the next middleware or route handler
            return await call_next(request)
            
        except AuthError as e:
            # Authentication error (invalid or expired token)
            # Redirect to login for browser requests, return JSON for API
            if "text/html" in request.headers.get("accept", ""):
                original_url = str(request.url)
                login_url = f"/auth/login?redirect_url={original_url}"
                return RedirectResponse(url=login_url, status_code=302)
            else:
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.message}
                )
        
        except Exception as e:
            # Unexpected error
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during authentication"}
            )


def get_current_user(request: Request):
    """
    Dependency to extract current user from request state
    
    Args:
        request: FastAPI request object with user info in state
    
    Returns:
        User information dict
    
    Raises:
        HTTPException: If user is not authenticated
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_permission(service: str, level: str):
    """
    Decorator to require specific service permission level
    
    Args:
        service: Service name (e.g., "tickets", "inventory")
        level: Required permission level (e.g., "read", "write", "admin")
    
    Returns:
        Decorator function
    
    Example:
        @router.get("/tickets")
        @require_permission("tickets", "read")
        def get_tickets():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            
            # Find request object in args or kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request and "request" in kwargs:
                request = kwargs["request"]
            
            if not request:
                raise HTTPException(
                    status_code=500,
                    detail="Request object not found in handler arguments"
                )
            
            # Get user from request state
            user = getattr(request.state, "user", None)
            if not user:
                raise HTTPException(status_code=401, detail="Not authenticated")
            
            # Check permission
            user_permissions = user.get("permissions", {})
            if not has_permission(user_permissions, service, level):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions for {service}"
                )
            
            # If permission check passes, call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
