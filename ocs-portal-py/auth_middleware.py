"""
Authentication middleware for FastAPI
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from auth_service import AuthenticationService
from auth_config import AuthConfig
from database import get_db

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for protected routes"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/", 
            "/auth/login", 
            "/auth/microsoft", 
            "/auth/callback",
            "/static",
            "/health",
            "/auth/status"
        ]
    
    async def dispatch(self, request: Request, call_next):
        print(f"DEBUG: Middleware dispatch called for {request.url.path}")
        
        # Skip authentication for excluded paths
        # Use exact match for root path, startswith for others
        path = request.url.path
        should_exclude = False
        
        for exclude_path in self.exclude_paths:
            if exclude_path == "/" and path == "/":
                # Exact match for root path only
                should_exclude = True
                break
            elif exclude_path != "/" and path.startswith(exclude_path):
                # Prefix match for other paths
                should_exclude = True
                break
        
        if should_exclude:
            print(f"DEBUG: Path {request.url.path} is excluded from auth")
            response = await call_next(request)
            return response
        
        print(f"DEBUG: Path {request.url.path} requires authentication")
        
        # Get session token from cookie
        session_token = request.cookies.get("session_token")
        if not session_token:
            # No token, redirect to login
            print(f"DEBUG: No session token found for {request.url.path}")
            return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
        
        # Validate token
        db = next(get_db())
        auth_service = AuthenticationService(db)
        
        try:
            print(f"DEBUG: Validating token for {request.url.path}")
            user_info = auth_service.validate_token(session_token)
            if not user_info:
                # Invalid token, redirect to login
                print(f"DEBUG: Invalid token for {request.url.path}")
                response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
                response.delete_cookie("session_token")
                return response
            
            print(f"DEBUG: Token valid for user {user_info.get('email')} on {request.url.path}")
            # Add user info to request state
            request.state.user = user_info
            request.state.session_token = session_token
            
            # Continue with request
            response = await call_next(request)
            
            # Update session activity (handled in auth service)
            return response
            
        except Exception as e:
            # Authentication error, redirect to login
            print(f"DEBUG: Auth error for {request.url.path}: {str(e)}")
            response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
            response.delete_cookie("session_token")
            return response
        finally:
            db.close()

def require_permission(required_permission: str, access_level: str = "read"):
    """
    Decorator to require specific permissions for a route
    
    Args:
        required_permission: The permission to check (e.g., 'tickets', 'inventory')
        access_level: The access level required ('read', 'write', 'admin')
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Implementation would go here
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_access_level(required_level: str):
    """
    Decorator to require specific access level for a route
    
    Args:
        required_level: The access level required ('user', 'admin', 'super_admin')
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Implementation would go here
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from request state"""
    if hasattr(request.state, 'user'):
        return request.state.user
    return None
