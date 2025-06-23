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

def verify_admin_access(current_user: dict) -> None:
    """Verify user has admin access"""
    user_access_level = current_user.get('access_level', '')
    if user_access_level not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

@router.get("/stats")
async def get_user_statistics(
    current_user: dict = Depends(get_current_user),
    import_service: UserImportService = Depends(get_user_import_service)
):
    """Get user import statistics"""
    verify_admin_access(current_user)
    
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
    verify_admin_access(current_user)
    
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
):
    """Import all student users from Azure AD All_Students group"""
    verify_admin_access(current_user)
    
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
    """Import all users from both Azure AD groups (All_Staff and All_Students)"""
    verify_admin_access(current_user)
    
    try:
        logger.info(f"Full user import initiated by {current_user.get('email', 'Unknown')}")
        
        # Run import in background for large datasets
        def run_import():
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Import both staff and students
                staff_result = loop.run_until_complete(import_service.import_all_staff())
                student_result = loop.run_until_complete(import_service.import_all_students())
                
                logger.info(f"Full import completed - Staff: {staff_result}, Students: {student_result}")
            except Exception as e:
                logger.error(f"Background full import failed: {e}")
        
        background_tasks.add_task(run_import)
        
        return {
            "success": True,
            "message": "Full user import started in background. Check logs for completion status.",
            "initiated_by": current_user.get('email')
        }
        
    except Exception as e:
        logger.error(f"Error starting full import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start full import: {str(e)}")

@router.get("/import/status")
async def get_import_status(
    current_user: dict = Depends(get_current_user),
    import_service: UserImportService = Depends(get_user_import_service)
):
    """Get the status of user import operations"""
    verify_admin_access(current_user)
    
    try:
        status = import_service.get_import_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting import status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get import status")

@router.get("/list")
async def list_users(
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List users with pagination and filtering"""
    verify_admin_access(current_user)
    
    try:
        # Build query
        query = db.query(User)
        
        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (User.display_name.ilike(search_filter)) |
                (User.email.ilike(search_filter)) |
                (User.first_name.ilike(search_filter)) |
                (User.last_name.ilike(search_filter))
            )
        
        # Apply department filter
        if department:
            query = query.join(UserDepartment).filter(UserDepartment.department_name == department)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        # Format response
        user_list = []
        for user in users:
            user_data = {
                "id": user.id,
                "azure_id": user.azure_id,
                "email": user.email,
                "display_name": user.display_name,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "access_level": user.access_level,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "departments": [dept.department_name for dept in user.departments] if user.departments else []
            }
            user_list.append(user_data)
        
        return {
            "success": True,
            "data": {
                "users": user_list,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": (total + per_page - 1) // per_page
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to list users")

@router.get("/departments/list")
async def list_departments(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all departments"""
    verify_admin_access(current_user)
    
    try:
        departments = db.query(UserDepartment.department_name).distinct().all()
        dept_list = [dept[0] for dept in departments if dept[0]]
        
        return {
            "success": True,
            "data": {
                "departments": sorted(dept_list)
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing departments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list departments")

@router.post("/sync/{user_id}")
async def sync_user_with_azure(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    import_service: UserImportService = Depends(get_user_import_service)
):
    """Sync a specific user's data with Azure AD"""
    verify_admin_access(current_user)
    
    try:
        logger.info(f"User sync initiated for {user_id} by {current_user.get('email', 'Unknown')}")
        
        result = await import_service.sync_user_with_azure(user_id)
        
        return {
            "success": True,
            "message": f"User {user_id} synced successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error syncing user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync user: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)"""
    verify_admin_access(current_user)
    
    try:
        # Find user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Don't allow deleting yourself
        if user.azure_id == current_user.get('user_id'):
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Delete user
        db.delete(user)
        db.commit()
        
        logger.info(f"User {user_id} deleted by {current_user.get('email', 'Unknown')}")
        
        return {
            "success": True,
            "message": f"User {user.email} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

@router.patch("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a user account"""
    verify_admin_access(current_user)
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = True
        db.commit()
        
        logger.info(f"User {user_id} activated by {current_user.get('email', 'Unknown')}")
        
        return {
            "success": True,
            "message": f"User {user.email} activated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error activating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate user")

@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate a user account"""
    verify_admin_access(current_user)
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Don't allow deactivating yourself
        if user.azure_id == current_user.get('user_id'):
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        
        user.is_active = False
        db.commit()
        
        logger.info(f"User {user_id} deactivated by {current_user.get('email', 'Unknown')}")
        
        return {
            "success": True,
            "message": f"User {user.email} deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate user")
