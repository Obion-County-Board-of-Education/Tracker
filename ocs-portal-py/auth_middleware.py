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

class AuthenticationMiddleware(BaseHTTPMiddleware):    """Middleware to handle authentication for protected routes"""
    
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
            print(f"DEBUG: User info contains: {list(user_info.keys())}")
            print(f"DEBUG: User permissions: {user_info.get('permissions', 'NOT FOUND')}")
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
    """Get current user from request state with enhanced permissions"""
    if hasattr(request.state, 'user'):
        user = request.state.user
        
        # Ensure permissions are properly populated
        if 'permissions' in user and isinstance(user['permissions'], dict):
            # Add convenience properties for template compatibility
            permissions = user['permissions']
            user['tickets_write'] = permissions.get('tickets_access') in ['write', 'admin']
            user['tickets_admin'] = permissions.get('tickets_access') == 'admin'
            user['purchasing_write'] = permissions.get('purchasing_access') in ['write', 'admin']
            user['purchasing_admin'] = permissions.get('purchasing_access') == 'admin'
            user['inventory_write'] = permissions.get('inventory_access') in ['write', 'admin']
            user['inventory_admin'] = permissions.get('inventory_access') == 'admin'
            user['forms_write'] = permissions.get('forms_access') in ['write', 'admin']
            user['forms_admin'] = permissions.get('forms_access') == 'admin'
            
        return user
    return None

async def get_menu_context(request: Request) -> dict:
    """Get menu context with role-based filtering"""
    try:
        current_user = get_current_user(request)
        print(f"DEBUG: get_menu_context - current_user: {current_user}")
        if not current_user:
            return {
                'user': None,
                'access_level': 'guest',
                'permissions': {},
                'menu_visibility': {},
                'is_authenticated': False            }
        
        access_level = current_user.get('access_level', 'student')
        permissions = current_user.get('permissions', {})
        
        print(f"DEBUG: get_menu_context - access_level: {access_level}")
        print(f"DEBUG: get_menu_context - permissions: {permissions}")
        
        # Determine what should be visible in the menu based on permissions
        menu_visibility = {
            'tickets': permissions.get('tickets_access', 'none') != 'none',
            'purchasing': permissions.get('purchasing_access', 'none') != 'none',
            'inventory': permissions.get('inventory_access', 'none') != 'none' and access_level in ['admin', 'super_admin'],
            'forms': permissions.get('forms_access', 'none') != 'none' and access_level in ['admin', 'super_admin'],
            'manage': access_level in ['admin', 'super_admin'],
            'admin': access_level in ['admin', 'super_admin']
        }
        
        # Generate menu items based on permissions
        menu_items = []
        
        if menu_visibility['tickets']:
            menu_items.append({
                'name': 'Tickets',
                'url': '/tickets',
                'icon': 'fa-ticket',
                'access_level': permissions.get('tickets_access'),
                'dropdown': [
                    {'name': 'New Tech Ticket', 'url': '/tickets/tech/new'},
                    {'name': 'Tech Tickets', 'url': '/tickets/tech/open'},
                    {'name': 'New Maintenance Request', 'url': '/tickets/maintenance/new'},
                    {'name': 'Maintenance Requests', 'url': '/tickets/maintenance/open'}
                ]
            })
        
        if menu_visibility['purchasing']:
            menu_items.append({
                'name': 'Purchasing',
                'url': '/purchasing',
                'icon': 'fa-shopping-cart',
                'access_level': permissions.get('purchasing_access'),
                'dropdown': [
                    {'name': 'New Requisition', 'url': '/purchasing/new'},
                    {'name': 'My Requisitions', 'url': '/purchasing/my'},
                    {'name': 'All Requisitions', 'url': '/purchasing/all'}
                ]
            })
        
        if menu_visibility['inventory']:
            menu_items.append({
                'name': 'Inventory',
                'url': '/inventory',
                'icon': 'fa-boxes-stacked',
                'access_level': permissions.get('inventory_access'),
                'dropdown': [
                    {'name': 'Add Inventory', 'url': '/inventory/add'},
                    {'name': 'View Inventory', 'url': '/inventory/view'},
                    {'name': 'Check Out Items', 'url': '/inventory/checkout'},
                    {'name': 'Check In Items', 'url': '/inventory/checkin'}
                ]
            })
        
        if menu_visibility['forms']:
            menu_items.append({
                'name': 'Forms',
                'url': '/forms',
                'icon': 'fa-file-alt',
                'access_level': permissions.get('forms_access'),
                'dropdown': [
                    {'name': 'Create Form', 'url': '/forms/new'},
                    {'name': 'View Forms', 'url': '/forms/list'},
                    {'name': 'Form Submissions', 'url': '/forms/submissions'}
                ]
            })
        
        if menu_visibility['manage']:
            menu_items.append({
                'name': 'Manage',
                'url': '/manage',
                'icon': 'fa-gears',
                'access_level': 'admin',
                'dropdown': [
                    {'name': 'Settings', 'url': '/manage/settings'},
                    {'name': 'System Logs', 'url': '/manage/logs'},
                    {'name': 'Other Management', 'url': '/manage/other'}
                ]
            })
        
        if menu_visibility['admin']:
            menu_items.append({
                'name': 'Admin',
                'url': '/admin',
                'icon': 'fa-user-gear',
                'access_level': 'admin',
                'dropdown': [
                    {'name': 'Users', 'url': '/users/list'},
                    {'name': 'Buildings', 'url': '/buildings/list'},
                    {'name': 'Reports', 'url': '/admin/reports'}
                ]
            })
        
        return {
            'user': current_user,
            'access_level': access_level,
            'permissions': permissions,
            'menu_visibility': menu_visibility,
            'menu_items': menu_items,
            'is_authenticated': True
        }
        
    except Exception as e:
        print(f"Error getting menu context: {e}")
        return {
            'user': None,
            'access_level': 'guest',
            'permissions': {},
            'menu_visibility': {},
            'menu_items': [],
            'is_authenticated': False
        }
