"""
Azure AD / Entra ID Authentication Service
"""
import msal
import requests
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
import sys
import os

# Handle imports for different execution contexts
try:
    from ocs_shared_models.models import UserSession, GroupRole, AuditLog
except ImportError:
    # Try alternative import path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from ocs_shared_models.models import UserSession, GroupRole, AuditLog

try:
    from .auth_config import AuthConfig
except ImportError:
    from auth_config import AuthConfig


class AuthenticationService:
    def __init__(self, db: Session):
        self.db = db
        self.config = AuthConfig
        self.msal_app = msal.ConfidentialClientApplication(
            client_id=self.config.AZURE_CLIENT_ID,
            client_credential=self.config.AZURE_CLIENT_SECRET,
            authority=self.config.AZURE_AUTHORITY
        )
    
    def get_auth_url(self, state: str = None) -> str:
        """Generate the authentication URL for Azure AD login"""
        return self.msal_app.get_authorization_request_url(
            scopes=self.config.SCOPE,
            state=state,
            redirect_uri=self.config.AZURE_REDIRECT_URI
        )
    
    def handle_auth_callback(self, authorization_code: str, state: str = None) -> Dict[str, Any]:
        """Handle the OAuth callback and get access token"""
        try:
            result = self.msal_app.acquire_token_by_authorization_code(
                code=authorization_code,
                scopes=self.config.SCOPE,
                redirect_uri=self.config.AZURE_REDIRECT_URI
            )
            
            if "error" in result:
                return {"error": result["error"], "error_description": result.get("error_description", "")}
            
            # Get user info using the access token
            user_info = self.get_user_info(result["access_token"])
            if "error" in user_info:
                return user_info
            
            return {
                "access_token": result["access_token"],
                "user_info": user_info,
                "expires_in": result.get("expires_in", 3600)
            }
            
        except Exception as e:
            return {"error": "token_exchange_failed", "error_description": str(e)}
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph API"""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Get basic user info
            user_response = requests.get(
                "https://graph.microsoft.com/v1.0/me?$select=id,userPrincipalName,displayName,givenName,surname,mail,extensionAttribute10",
                headers=headers,
                timeout=10
            )
            
            if user_response.status_code != 200:
                return {"error": "user_info_failed", "error_description": f"Failed to get user info: {user_response.status_code}"}
            
            user_data = user_response.json()
            
            # Get user's group memberships
            groups_response = requests.get(
                "https://graph.microsoft.com/v1.0/me/memberOf?$select=id,displayName",
                headers=headers,
                timeout=10
            )
            
            groups_data = []
            if groups_response.status_code == 200:
                groups_data = groups_response.json().get("value", [])
            
            return {
                "user_data": user_data,
                "groups_data": groups_data
            }
            
        except Exception as e:
            return {"error": "user_info_failed", "error_description": str(e)}
    
    def determine_permissions(self, user_data: Dict, groups_data: List[Dict]) -> Dict[str, Any]:
        """Determine user permissions based on Azure AD groups and attributes"""
        try:
            # Get all group role mappings from database
            group_roles = self.db.query(GroupRole).all()
            
            permissions = {
                'access_level': 'student',  # Default access level
                'tickets_access': 'write',
                'inventory_access': 'none',
                'purchasing_access': 'none',
                'forms_access': 'none',
                'matched_groups': [],
                'allowed_departments': []
            }
            
            # Check group memberships - safely handle None values
            user_group_ids = [group.get('id') for group in groups_data if group.get('id')]
            user_group_names = [group.get('displayName', '').lower() for group in groups_data if group.get('displayName')]
            
            # Check extensionAttribute10 for Director of Schools - safely handle None
            extension_attr_10 = user_data.get('extensionAttribute10') or ''
            
            for role in group_roles:
                matched = False
                
                # Check Azure AD group ID match
                if role.azure_group_id and role.azure_group_id in user_group_ids:
                    matched = True
                
                # Check group name match (case insensitive)
                elif role.group_name and role.group_name.lower() in user_group_names:
                    matched = True
                
                # Check extension attribute match
                elif (role.azure_user_attribute == 'extensionAttribute10' and 
                      role.azure_user_attribute_value and
                      extension_attr_10 == role.azure_user_attribute_value):
                    matched = True
                
                if matched:
                    permissions['matched_groups'].append(role.group_name)
                    
                    # Use highest access level found
                    if self._compare_access_levels(role.access_level, permissions['access_level']):
                        permissions['access_level'] = role.access_level
                        permissions['tickets_access'] = role.tickets_access
                        permissions['inventory_access'] = role.inventory_access
                        permissions['purchasing_access'] = role.purchasing_access
                        permissions['forms_access'] = role.forms_access
                        
                        if role.allowed_departments:
                            permissions['allowed_departments'].extend(role.allowed_departments)
            
            return permissions
            
        except Exception as e:
            # If permission determination fails, return safe defaults
            print(f"Error determining permissions: {str(e)}")
            return {
                'access_level': 'student',
                'tickets_access': 'write',
                'inventory_access': 'none',
                'purchasing_access': 'none',
                'forms_access': 'none',
                'matched_groups': [],
                'allowed_departments': []
            }
    
    def _compare_access_levels(self, new_level: str, current_level: str) -> bool:
        """Compare access levels and return True if new_level is higher"""
        hierarchy = ['student', 'staff', 'admin', 'super_admin']
        try:
            return hierarchy.index(new_level) > hierarchy.index(current_level)
        except ValueError:
            return False
    
    def create_session(self, user_id: str, permissions: Dict[str, Any], ip_address: str = None) -> str:
        """Create a new user session and return JWT token"""
        
        # Clean up old sessions first
        self._cleanup_old_sessions(user_id)
        
        # Create JWT token
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.config.JWT_EXPIRATION_HOURS)
        }
        
        token = jwt.encode(payload, self.config.JWT_SECRET, algorithm=self.config.JWT_ALGORITHM)
        
        # Store session in database
        session = UserSession(
            user_id=user_id,
            session_token=token,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=self.config.JWT_EXPIRATION_HOURS),
            ip_address=ip_address,
            permissions=permissions
        )
        
        self.db.add(session)
        
        # Log the login
        if self.config.ENABLE_AUDIT_LOGGING:
            audit_log = AuditLog(
                user_id=user_id,
                action_type='login',
                resource_type='session',
                details={'login_method': 'azure_ad', 'access_level': permissions['access_level']},
                ip_address=ip_address
            )
            self.db.add(audit_log)
        
        self.db.commit()
        
        return token
    
    def _cleanup_old_sessions(self, user_id: str):
        """Remove old/expired sessions for a user"""
        
        # Remove expired sessions
        expired_sessions = self.db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        for session in expired_sessions:
            self.db.delete(session)
        
        # Limit concurrent sessions
        user_sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.expires_at > datetime.utcnow()
        ).order_by(UserSession.created_at.desc()).all()
        
        if len(user_sessions) >= self.config.MAX_CONCURRENT_SESSIONS:
            # Remove oldest sessions
            sessions_to_remove = user_sessions[self.config.MAX_CONCURRENT_SESSIONS-1:]
            for session in sessions_to_remove:
                self.db.delete(session)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user info"""
        try:
            payload = jwt.decode(token, self.config.JWT_SECRET, algorithms=[self.config.JWT_ALGORITHM])
            
            # Check if session exists in database
            session = self.db.query(UserSession).filter(
                UserSession.session_token == token,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    def logout(self, token: str, ip_address: str = None) -> bool:
        """Logout user and invalidate session"""
        try:
            # Decode token to get user info
            payload = jwt.decode(token, self.config.JWT_SECRET, algorithms=[self.config.JWT_ALGORITHM])
            user_id = payload.get('user_id')
            
            # Remove session from database
            session = self.db.query(UserSession).filter(
                UserSession.session_token == token
            ).first()
            
            if session:
                self.db.delete(session)
                
                # Log the logout
                if self.config.ENABLE_AUDIT_LOGGING and user_id:
                    audit_log = AuditLog(
                        user_id=user_id,
                        action_type='logout',
                        resource_type='session',
                        details={'logout_method': 'manual'},
                        ip_address=ip_address
                    )
                    self.db.add(audit_log)
                
                self.db.commit()
                return True
                
        except Exception:
            # Token was invalid anyway
            pass
        
        return False


# Export the service for imports
__all__ = ["AuthenticationService"]
