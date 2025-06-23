"""
Azure AD / Entra ID Authentication Service
"""
print("DEBUG: Starting auth_service imports...")

import msal
import requests
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
import sys
import os

print("DEBUG: Basic imports completed")

# Handle imports for different execution contexts
try:
    from ocs_shared_models.models import UserSession, GroupRole, AuditLog
    print("DEBUG: Shared models imported directly")
except ImportError:
    # Try alternative import path
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from ocs_shared_models.models import UserSession, GroupRole, AuditLog
    print("DEBUG: Shared models imported via alternative path")

try:
    from .auth_config import AuthConfig
    print("DEBUG: Auth config imported with relative import")
except ImportError:
    from auth_config import AuthConfig
    print("DEBUG: Auth config imported with absolute import")

print("DEBUG: About to define AuthenticationService class...")

class AuthenticationService:
    def __init__(self, db: Session):
        print("DEBUG: AuthenticationService.__init__ called")
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
            
            if "access_token" in result:
                return result
            else:
                raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
                
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def get_application_token(self) -> Dict[str, Any]:
        """Get application token for Microsoft Graph API using client credentials"""
        try:
            result = self.msal_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            
            if "access_token" in result:
                return result
            else:
                raise Exception(f"Failed to acquire application token: {result.get('error_description', 'Unknown error')}")
                
        except Exception as e:
            raise Exception(f"Application authentication failed: {str(e)}")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get user profile
        user_response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        if user_response.status_code != 200:
            raise Exception("Failed to get user information")
        
        user_data = user_response.json()
          # Get user's group memberships
        groups_response = requests.get('https://graph.microsoft.com/v1.0/me/memberOf', headers=headers)
        groups_data = []
        
        if groups_response.status_code == 200:
            groups_data = groups_response.json().get('value', [])
        
        return {
            'user': user_data,
            'groups': groups_data
        }
    
    def determine_user_permissions(self, user_data: Dict, groups_data: List[Dict]) -> Dict[str, Any]:
        """Determine user permissions based on Azure AD groups and attributes"""
        
        try:
            email = user_data.get('mail', '').lower()
            print(f"DEBUG: Determining permissions for {email}")
            
            # Get all group role mappings
            group_roles = self.db.query(GroupRole).all()
            
            # Initialize with NO access (most restrictive)
            permissions = {
                'access_level': 'none',  # Default to no access
                'tickets_access': 'none',
                'inventory_access': 'none',
                'purchasing_access': 'none',
                'forms_access': 'none',
                'matched_groups': [],
                'allowed_departments': [],
                'services': []  # Add services list for template compatibility
            }
            
            # Check group memberships - safely handle None values
            user_group_ids = [group.get('id') for group in groups_data if group.get('id')]
            user_group_names = [group.get('displayName', '').lower() for group in groups_data if group.get('displayName')]
            
            print(f"DEBUG: User groups: {user_group_names}")
            
            # Check extensionAttribute10 for Director of Schools - safely handle None
            extension_attr_10 = user_data.get('extensionAttribute10') or ''
            print(f"DEBUG: Extension attribute 10: '{extension_attr_10}'")
            
            matched_any_group = False
            
            for role in group_roles:
                matched = False
                
                # Check Azure AD group ID match
                if role.azure_group_id and role.azure_group_id in user_group_ids:
                    matched = True
                    print(f"DEBUG: Matched by group ID: {role.group_name}")
                
                # Check group name match (case insensitive)
                elif role.group_name and role.group_name.lower() in user_group_names:
                    matched = True
                    print(f"DEBUG: Matched by group name: {role.group_name}")
                
                # Check extension attribute match
                elif (role.azure_user_attribute == 'extensionAttribute10' and 
                      role.azure_user_attribute_value and
                      extension_attr_10 == role.azure_user_attribute_value):
                    matched = True
                    print(f"DEBUG: Matched by extension attribute: {role.group_name}")
                
                if matched:
                    matched_any_group = True
                    permissions['matched_groups'].append(role.group_name)
                    
                    # Use highest access level found
                    if self._compare_access_levels(role.access_level, permissions['access_level']):
                        print(f"DEBUG: Upgrading access level from {permissions['access_level']} to {role.access_level}")
                        permissions['access_level'] = role.access_level
                        permissions['tickets_access'] = role.tickets_access
                        permissions['inventory_access'] = role.inventory_access
                        permissions['purchasing_access'] = role.purchasing_access
                        permissions['forms_access'] = role.forms_access
                        
                        if role.allowed_departments:
                            permissions['allowed_departments'].extend(role.allowed_departments)
            
            # Build services list based on permissions
            services = []
            if permissions['tickets_access'] != 'none':
                services.append('tickets')
            if permissions['purchasing_access'] != 'none':
                services.append('purchasing')
            if permissions['inventory_access'] != 'none':
                services.append('inventory')
            if permissions['forms_access'] != 'none':
                services.append('forms')
            if permissions['access_level'] in ['admin', 'super_admin']:
                services.append('admin')
            
            permissions['services'] = services
            
            if not matched_any_group:
                print(f"DEBUG: No group matches found for {email}")
            else:
                print(f"DEBUG: Final permissions for {email}: {permissions}")
            
            return permissions
            
        except Exception as e:
            # If permission determination fails, return safe defaults (no access)
            print(f"ERROR determining permissions: {str(e)}")
            return {
                'access_level': 'none',
                'tickets_access': 'none',
                'inventory_access': 'none',
                'purchasing_access': 'none',
                'forms_access': 'none',
                'matched_groups': [],
                'allowed_departments': [],
                'services': []
            }
    
    def _compare_access_levels(self, new_level: str, current_level: str) -> bool:
        """Compare access levels and return True if new_level is higher"""
        level_hierarchy = {
            'none': 0,
            'student': 1,
            'staff': 2,
            'admin': 3,
            'super_admin': 4
        }
        return level_hierarchy.get(new_level, 0) > level_hierarchy.get(current_level, 0)
    
    def create_user_session(self, user_data: Dict, permissions: Dict, ip_address: str = None) -> str:
        """Create a new user session and return JWT token"""
        
        user_id = user_data['id']
        email = user_data['mail'] or user_data['userPrincipalName']
        display_name = user_data['displayName']
        
        # Create JWT payload
        payload = {
            'user_id': user_id,
            'email': email,
            'display_name': display_name,
            'access_level': permissions['access_level'],
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(hours=self.config.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        
        # Generate JWT token
        token = jwt.encode(payload, self.config.JWT_SECRET, algorithm=self.config.JWT_ALGORITHM)
        
        # Check for existing sessions and clean up old ones
        self._cleanup_old_sessions(user_id)
        
        # Create session record
        session = UserSession(
            user_id=user_id,
            email=email,
            display_name=display_name,
            access_level=permissions['access_level'],
            azure_groups=permissions['matched_groups'],
            effective_permissions=permissions,
            session_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=self.config.JWT_EXPIRATION_HOURS)
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
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            self.db.commit()
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def logout_user(self, token: str, ip_address: str = None):
        """Logout user and invalidate session"""
        try:
            payload = jwt.decode(token, self.config.JWT_SECRET, algorithms=[self.config.JWT_ALGORITHM])
            user_id = payload.get('user_id')
            
            # Remove session from database
            session = self.db.query(UserSession).filter(
                UserSession.session_token == token
            ).first()
            
            if session:
                self.db.delete(session)
                
                # Log the logout
                if self.config.ENABLE_AUDIT_LOGGING:
                    audit_log = AuditLog(
                        user_id=user_id,
                        action_type='logout',
                        resource_type='session',
                        details={'logout_method': 'manual'},
                        ip_address=ip_address
                    )
                    self.db.add(audit_log)
                
                self.db.commit()                
        except Exception:
            # Token was invalid anyway
            pass


# Export the service for imports
__all__ = ["AuthenticationService"]
