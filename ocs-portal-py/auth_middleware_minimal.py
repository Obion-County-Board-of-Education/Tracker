"""
Minimal Authentication Middleware for Testing
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional, Dict

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Minimal auth middleware that allows all requests"""
    
    async def dispatch(self, request: Request, call_next):
        # For now, just allow all requests through
        request.state.user = {
            "user_id": "test_user",
            "permissions": {
                "access_level": "admin",
                "tickets_access": "write",
                "inventory_access": "read",
                "purchasing_access": "read",
                "forms_access": "write"
            }
        }
        response = await call_next(request)
        return response

def get_current_user(request: Request) -> Dict:
    """Get current user from request state"""
    return getattr(request.state, 'user', {
        "user_id": "test_user",
        "permissions": {
            "access_level": "admin",
            "tickets_access": "write",
            "inventory_access": "read",
            "purchasing_access": "read", 
            "forms_access": "write"
        }
    })
