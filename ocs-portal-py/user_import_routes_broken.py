"""
User Import API Routes for OCS Portal
Handles Azure AD user import and management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from database import get_db
from user_import_service import UserImportService
from auth_middleware import get_current_user
from ocs_shared_models.models import User, UserDepartment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/users", tags=["User Management"])

def get_user_import_service(db: Session = Depends(get_db)) -> UserImportService:
    """Dependency to get user import service"""
    return UserImportService(db)

@router.get("/stats")
async def get_user_statistics(
    current_user: dict = Depends(get_current_user),
    import_service: UserImportService = Depends(get_user_import_service)
):
    """Get user import statistics"""
    # Verify admin access
    user_access_level = current_user.get('access_level', '')
    if user_access_level not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        stats = import_service.get_import_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user statistics")

@router.post("/import/staff")
async def import_staff_users(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    import_service: UserImportService = Depends(get_user_import_service)
):
    """Import all staff users from Azure AD All_Staff group"""
    # Verify admin access
    user_access_level = current_user.get('access_level', '')
    if user_access_level not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        logger.info(f"Staff import initiated by {current_user.get('email', 'Unknown')}")
        
        # Run import in background for large datasets
        def run_import():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(import_service.import_all_staff())
                logger.info(f"Staff import completed: {result}")
            except Exception as e:
                logger.error(f"Background staff import failed: {e}")
        
        background_tasks.add_task(run_import)
        
        return {
            "success": True,
            "message": "Staff import started in background. Check logs for completion status.",
            "initiated_by": current_user.get('email')
        }
        
    except Exception as e:
        logger.error(f"Error starting staff import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start staff import: {str(e)}")

@router.post("/import/students")
async def import_student_users(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    import_service: UserImportService = Depends(get_user_import_service)
):    """Import all student users from Azure AD All_Students group"""
    # Verify admin access
    user_access_level = current_user.get('access_level', '')
    if user_access_level not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        logger.info(f"Student import initiated by {current_user.get('email', 'Unknown')}")
        
        # Run import in background for large datasets
        def run_import():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(import_service.import_all_students())
                logger.info(f"Student import completed: {result}")
            except Exception as e:
                logger.error(f"Background student import failed: {e}")
        
        background_tasks.add_task(run_import)
        
        return {
            "success": True,
            "message": "Student import started in background. Check logs for completion status.",
            "initiated_by": current_user.get('email')
        }
        
    except Exception as e:
        logger.error(f"Error starting student import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start student import: {str(e)}")

@router.post("/import/all")
async def import_all_users(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    import_service: UserImportService = Depends(get_user_import_service)
):
    """Import all users (both staff and students) from Azure AD"""
    # Verify admin access
    if not current_user.get('roles') or 'super_admin' not in current_user.get('roles', []):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        logger.info(f"Full user import initiated by {current_user.get('email', 'Unknown')}")
        
        # Run import in background for large datasets
        def run_import():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(import_service.sync_user_profiles())
                logger.info(f"Full user import completed: {result}")
            except Exception as e:
                logger.error(f"Background full import failed: {e}")
        
        background_tasks.add_task(run_import)
        
        return {
            "success": True,
            "message": "Full user import started in background. This includes both staff and students.",
            "initiated_by": current_user.get('email')
        }
        
    except Exception as e:
        logger.error(f"Error starting full user import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start full user import: {str(e)}")

@router.post("/sync")
async def sync_user_profiles(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    import_service: UserImportService = Depends(get_user_import_service)
):
    """Sync existing user profiles with latest Azure AD data"""
    # Verify admin access
    if not current_user.get('roles') or 'super_admin' not in current_user.get('roles', []):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        logger.info(f"User profile sync initiated by {current_user.get('email', 'Unknown')}")
        
        # Run sync in background
        def run_sync():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(import_service.sync_user_profiles())
                logger.info(f"User profile sync completed: {result}")
            except Exception as e:
                logger.error(f"Background sync failed: {e}")
        
        background_tasks.add_task(run_sync)
        
        return {
            "success": True,
            "message": "User profile sync started in background.",
            "initiated_by": current_user.get('email')
        }
        
    except Exception as e:
        logger.error(f"Error starting user sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start user sync: {str(e)}")

@router.get("/list")
async def list_users(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    user_type: Optional[str] = None,
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List users with pagination and filtering"""
    # Verify admin access
    if not current_user.get('roles') or 'super_admin' not in current_user.get('roles', []):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        # Build query
        query = db.query(User)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.display_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.department.ilike(search_term))
            )
        
        if user_type:
            query = query.filter(User.user_type == user_type)
            
        if department:
            query = query.filter(User.department.ilike(f"%{department}%"))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        # Format response
        user_data = []
        for user in users:
            user_dict = {
                "id": user.id,
                "display_name": user.display_name,
                "email": user.email,
                "user_type": user.user_type,
                "department": user.department,
                "job_title": user.job_title,
                "office_location": user.office_location,
                "is_active": user.is_active,
                "imported_at": user.imported_at.isoformat() if user.imported_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            user_data.append(user_dict)
        
        return {
            "success": True,
            "data": {
                "users": user_data,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                    "total_pages": (total_count + per_page - 1) // per_page
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")

@router.get("/{user_id}")
async def get_user_details(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific user"""
    # Verify admin access
    if not current_user.get('roles') or 'super_admin' not in current_user.get('roles', []):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user departments
        departments = db.query(UserDepartment).filter(UserDepartment.user_id == user_id).all()
        
        user_data = {
            "id": user.id,
            "azure_user_id": user.azure_user_id,
            "display_name": user.display_name,
            "email": user.email,
            "user_principal_name": user.user_principal_name,
            "given_name": user.given_name,
            "surname": user.surname,
            "job_title": user.job_title,
            "department": user.department,
            "office_location": user.office_location,
            "employee_id": user.employee_id,
            "employee_type": user.employee_type,
            "manager_id": user.manager_id,
            "building_assignment": user.building_assignment,
            "grade_level": user.grade_level,
            "user_type": user.user_type,
            "is_active": user.is_active,
            "roles": user.roles,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "imported_at": user.imported_at.isoformat() if user.imported_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "departments": [
                {
                    "department_name": dept.department_name,
                    "building_name": dept.building_name,
                    "is_primary": dept.is_primary,
                    "role_in_department": dept.role_in_department
                }
                for dept in departments
            ]
        }
        
        return {
            "success": True,
            "data": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user details for ID {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user details")

@router.get("/departments/list")
async def list_departments(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all departments with user counts"""
    # Verify admin access
    if not current_user.get('roles') or 'super_admin' not in current_user.get('roles', []):
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    try:
        # Get distinct departments from users table
        dept_query = db.query(User.department, User.user_type).filter(
            User.department.isnot(None),
            User.department != ''
        ).all()
        
        # Count users by department and type
        department_stats = {}
        for dept, user_type in dept_query:
            if dept not in department_stats:
                department_stats[dept] = {'staff': 0, 'student': 0, 'total': 0}
            
            department_stats[dept][user_type] = department_stats[dept].get(user_type, 0) + 1
            department_stats[dept]['total'] += 1
        
        # Format response
        departments = [
            {
                "name": dept,
                "staff_count": stats['staff'],
                "student_count": stats['student'],
                "total_count": stats['total']
            }
            for dept, stats in department_stats.items()
        ]
        
        # Sort by total count descending
        departments.sort(key=lambda x: x['total_count'], reverse=True)
        
        return {
            "success": True,
            "data": {
                "departments": departments,
                "total_departments": len(departments)
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing departments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list departments")
