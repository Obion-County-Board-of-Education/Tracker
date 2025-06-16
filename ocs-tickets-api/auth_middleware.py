"""
Authentication middleware for FastAPI microservices
Validates the JWT token passed from the portal
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import os
from typing import Optional, Dict, Any

# Get configuration from environment or use defaults
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key_change_this_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for protected routes"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for excluded paths
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
            response = await call_next(request)
            return response
        
        # Get token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"}
            )
        
        token = authorization.replace("Bearer ", "")
        user_info = validate_token(token)
        
        if not user_info:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"}
            )
        
        # Add user info to request state
        request.state.user = user_info
        
        # Continue with request
        response = await call_next(request)
        return response

def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate JWT token and return user info"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from request state"""
    if hasattr(request.state, "user"):
        return request.state.user
    return None

def has_permission(request: Request, service: str, access_level: str = "read") -> bool:
    """Check if the user has permission for a specific service"""
    user = get_current_user(request)
    if not user:
        return False
    
    # Get permissions from user
    permissions = user.get("permissions", {})
    
    # Service-specific permission check
    service_key = f"{service}_access"
    user_access = permissions.get(service_key, "none")
    
    # Access level hierarchy: none < read < write < admin
    access_hierarchy = {
        "none": 0,
        "read": 1,
        "write": 2,
        "admin": 3
    }
    
    return access_hierarchy.get(user_access, 0) >= access_hierarchy.get(access_level, 0)
