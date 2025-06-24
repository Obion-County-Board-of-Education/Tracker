"""
User Import Service for OCS Tracker
Handles importing users from Azure AD groups (All_Staff and All_Students)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import httpx
from fastapi import HTTPException

from database import get_db
from auth_service import AuthenticationService
from ocs_shared_models.models import User, UserDepartment

logger = logging.getLogger(__name__)

class UserImportService:
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthenticationService(db)
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        
    def get_access_token(self) -> str:
        """Get access token for Microsoft Graph API"""
        try:
            token_response = self.auth_service.get_application_token()
            return token_response.get('access_token')
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise HTTPException(status_code=500, detail="Failed to authenticate with Microsoft Graph")
    
    async def get_group_id_by_name(self, group_name: str) -> Optional[str]:
        """Get Azure AD group ID by group name"""
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Search for group by display name
        url = f"{self.graph_base_url}/groups"
        params = {
            "$filter": f"displayName eq '{group_name}'",
            "$select": "id,displayName"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                groups = data.get('value', [])
                
                if groups:
                    group_id = groups[0]['id']
                    logger.info(f"Found group '{group_name}' with ID: {group_id}")
                    return group_id
                else:
                    logger.warning(f"Group '{group_name}' not found")
                    return None
                    
            except httpx.HTTPError as e:
                logger.error(f"HTTP error getting group ID for '{group_name}': {e}")
                return None
            except Exception as e:
                logger.error(f"Error getting group ID for '{group_name}': {e}")
                return None
    
    async def get_group_members(self, group_id: str, batch_size: int = 100) -> List[Dict[str, Any]]:
        """Get all members of an Azure AD group with pagination"""
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        all_members = []
        url = f"{self.graph_base_url}/groups/{group_id}/members"
        params = {
            "$select": "id,userPrincipalName,mail,displayName,givenName,surname,jobTitle,department,officeLocation,employeeId,employeeType,manager",
            "$top": batch_size
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while url:
                try:
                    response = await client.get(url, headers=headers, params=params if url == f"{self.graph_base_url}/groups/{group_id}/members" else None)
                    response.raise_for_status()
                    
                    data = response.json()
                    members = data.get('value', [])
                    all_members.extend(members)
                    
                    # Get next page URL
                    url = data.get('@odata.nextLink')
                    params = None  # Clear params for subsequent requests
                    
                    logger.info(f"Retrieved {len(members)} members, total so far: {len(all_members)}")
                    
                    # Small delay to respect rate limits
                    await asyncio.sleep(0.1)
                    
                except httpx.HTTPError as e:
                    logger.error(f"HTTP error getting group members: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error getting group members: {e}")
                    break
        
        logger.info(f"Total members retrieved: {len(all_members)}")
        return all_members
    
    def map_azure_user_to_db(self, azure_user: Dict[str, Any], user_type: str) -> Dict[str, Any]:
        """Map Azure AD user data to database user model"""
        return {
            'azure_user_id': azure_user.get('id'),
            'email': azure_user.get('mail') or azure_user.get('userPrincipalName'),
            'user_principal_name': azure_user.get('userPrincipalName'),
            'display_name': azure_user.get('displayName', ''),
            'given_name': azure_user.get('givenName'),
            'surname': azure_user.get('surname'),
            'job_title': azure_user.get('jobTitle'),
            'department': azure_user.get('department'),
            'office_location': azure_user.get('officeLocation'),
            'employee_id': azure_user.get('employeeId'),
            'employee_type': azure_user.get('employeeType'),
            'user_type': user_type,
            'is_active': True,
            'imported_at': datetime.utcnow()
        }
    
    def create_or_update_user(self, user_data: Dict[str, Any]) -> User:
        """Create new user or update existing user in database"""
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                User.azure_user_id == user_data['azure_user_id']
            ).first()
            
            if existing_user:
                # Update existing user
                for key, value in user_data.items():
                    if key not in ['id', 'created_at']:  # Don't update these fields
                        setattr(existing_user, key, value)
                existing_user.updated_at = datetime.utcnow()
                
                logger.debug(f"Updated user: {existing_user.display_name}")
                return existing_user
            else:
                # Create new user
                new_user = User(**user_data)
                self.db.add(new_user)
                self.db.flush()  # Get the ID
                
                logger.debug(f"Created new user: {new_user.display_name}")
                return new_user
                
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating/updating user {user_data.get('display_name')}: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating/updating user {user_data.get('display_name')}: {e}")
            raise
    
    def create_user_department(self, user: User, department_info: Dict[str, Any]):
        """Create user department assignment"""
        if not department_info.get('department'):
            return
            
        try:
            # Check if department assignment already exists
            existing_dept = self.db.query(UserDepartment).filter(
                UserDepartment.user_id == user.id,
                UserDepartment.department_name == department_info['department']
            ).first()
            
            if not existing_dept:
                user_dept = UserDepartment(
                    user_id=user.id,
                    department_name=department_info['department'],
                    building_name=department_info.get('building', 'Unknown'),
                    is_primary=True,
                    role_in_department=department_info.get('job_title', 'Staff')
                )
                self.db.add(user_dept)
                logger.debug(f"Created department assignment for {user.display_name}: {department_info['department']}")
                
        except Exception as e:
            logger.error(f"Error creating department assignment for {user.display_name}: {e}")
    
    async def import_all_staff(self) -> Dict[str, Any]:
        """Import all users from All_Staff Azure AD group"""
        logger.info("Starting All_Staff import...")
        
        # Get group ID
        group_id = await self.get_group_id_by_name("All_Staff")
        if not group_id:
            raise HTTPException(status_code=404, detail="All_Staff group not found in Azure AD")
        
        # Get group members
        staff_members = await self.get_group_members(group_id)
        
        import_results = {
            'total_found': len(staff_members),
            'imported': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }
        
        for member in staff_members:
            try:
                user_data = self.map_azure_user_to_db(member, 'staff')
                
                # Check if this is new or existing
                existing = self.db.query(User).filter(User.azure_user_id == user_data['azure_user_id']).first()
                is_new = existing is None
                
                user = self.create_or_update_user(user_data)
                
                # Create department assignment
                self.create_user_department(user, {
                    'department': member.get('department'),
                    'building': member.get('officeLocation'),
                    'job_title': member.get('jobTitle')
                })
                
                if is_new:
                    import_results['imported'] += 1
                else:
                    import_results['updated'] += 1
                    
            except Exception as e:
                import_results['errors'] += 1
                error_msg = f"Error importing {member.get('displayName', 'Unknown')}: {str(e)}"
                import_results['error_details'].append(error_msg)
                logger.error(error_msg)
                continue
        
        # Commit all changes
        try:
            self.db.commit()
            logger.info(f"All_Staff import completed: {import_results}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit All_Staff import: {e}")
            raise HTTPException(status_code=500, detail="Failed to save imported users")
        
        return import_results
    
    async def import_all_students(self) -> Dict[str, Any]:
        """Import all users from All_Students Azure AD group"""
        logger.info("Starting All_Students import...")
        
        # Get group ID
        group_id = await self.get_group_id_by_name("All_Students")
        if not group_id:
            raise HTTPException(status_code=404, detail="All_Students group not found in Azure AD")
        
        # Get group members
        student_members = await self.get_group_members(group_id)
        
        import_results = {
            'total_found': len(student_members),
            'imported': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }
        
        for member in student_members:
            try:
                user_data = self.map_azure_user_to_db(member, 'student')
                
                # Check if this is new or existing
                existing = self.db.query(User).filter(User.azure_user_id == user_data['azure_user_id']).first()
                is_new = existing is None
                
                user = self.create_or_update_user(user_data)
                
                # For students, create department based on grade level or building
                self.create_user_department(user, {
                    'department': f"Students - {member.get('department', 'General')}",
                    'building': member.get('officeLocation', 'Main Campus'),
                    'job_title': 'Student'
                })
                
                if is_new:
                    import_results['imported'] += 1
                else:
                    import_results['updated'] += 1
                    
            except Exception as e:
                import_results['errors'] += 1
                error_msg = f"Error importing {member.get('displayName', 'Unknown')}: {str(e)}"
                import_results['error_details'].append(error_msg)
                logger.error(error_msg)
                continue
        
        # Commit all changes
        try:
            self.db.commit()
            logger.info(f"All_Students import completed: {import_results}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit All_Students import: {e}")
            raise HTTPException(status_code=500, detail="Failed to save imported users")
        
        return import_results
    
    async def sync_user_profiles(self) -> Dict[str, Any]:
        """Sync existing user profiles with latest Azure AD data"""
        logger.info("Starting user profile sync...")
        
        # Import both groups to update existing users
        staff_results = await self.import_all_staff()
        student_results = await self.import_all_students()
        
        sync_results = {
            'staff_updated': staff_results['updated'],
            'staff_new': staff_results['imported'],
            'students_updated': student_results['updated'],
            'students_new': student_results['imported'],
            'total_errors': staff_results['errors'] + student_results['errors'],
            'error_details': staff_results['error_details'] + student_results['error_details']
        }
        
        logger.info(f"User profile sync completed: {sync_results}")
        return sync_results
    
    def get_import_statistics(self) -> Dict[str, Any]:
        """Get statistics about imported users"""
        try:
            total_users = self.db.query(User).count()
            staff_count = self.db.query(User).filter(User.user_type == 'staff').count()
            student_count = self.db.query(User).filter(User.user_type == 'student').count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            
            # Recent imports (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_imports = self.db.query(User).filter(User.imported_at >= yesterday).count()
            
            return {
                'total_users': total_users,
                'staff_count': staff_count,
                'student_count': student_count,
                'active_users': active_users,
                'recent_imports_24h': recent_imports,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting import statistics: {e}")
            return {
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }
        
    async def run_scheduled_import(self) -> Dict[str, Any]:
        """Run a complete scheduled import of all users (staff and students)"""
        try:
            logger.info("🔄 Starting scheduled user import...")
            start_time = datetime.utcnow()
            
            results = {
                'success': True,
                'started_at': start_time.isoformat(),
                'staff_import': None,
                'student_import': None,
                'profile_sync': None,
                'total_imported': 0,
                'total_updated': 0,
                'errors': []
            }
            
            # Import staff users
            try:
                logger.info("📋 Importing staff users...")
                staff_result = await self.import_all_staff()
                results['staff_import'] = staff_result
                
                if staff_result.get('success'):
                    results['total_imported'] += staff_result.get('imported_count', 0)
                    results['total_updated'] += staff_result.get('updated_count', 0)
                else:
                    results['errors'].append(f"Staff import failed: {staff_result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                error_msg = f"Staff import error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # Import student users
            try:
                logger.info("🎓 Importing student users...")
                student_result = await self.import_all_students()
                results['student_import'] = student_result
                
                if student_result.get('success'):
                    results['total_imported'] += student_result.get('imported_count', 0)
                    results['total_updated'] += student_result.get('updated_count', 0)
                else:
                    results['errors'].append(f"Student import failed: {student_result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                error_msg = f"Student import error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # Sync user profiles
            try:
                logger.info("🔄 Syncing user profiles...")
                sync_result = await self.sync_user_profiles()
                results['profile_sync'] = sync_result
                
                if not sync_result.get('success'):
                    results['errors'].append(f"Profile sync failed: {sync_result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                error_msg = f"Profile sync error: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # Calculate completion time
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            results['completed_at'] = end_time.isoformat()
            results['duration_seconds'] = duration
            
            # Determine overall success
            if results['errors']:
                results['success'] = False
                results['message'] = f"Import completed with {len(results['errors'])} errors"
                logger.warning(f"⚠️ Scheduled import completed with errors: {results['message']}")
            else:
                results['message'] = f"Successfully imported {results['total_imported']} users and updated {results['total_updated']} users"
                logger.info(f"✅ Scheduled import completed successfully: {results['message']}")
            
            return results
            
        except Exception as e:
            error_msg = f"Scheduled import failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'message': error_msg,
                'started_at': datetime.utcnow().isoformat(),
                'errors': [error_msg]
            }
