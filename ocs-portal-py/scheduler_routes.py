"""
OCS Portal - Scheduler Routes
API endpoints for managing scheduled tasks
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/admin/scheduler", tags=["scheduler"])

# Global scheduler service instance
_scheduler_service: Optional[object] = None

def set_scheduler_service(service):
    """Set the global scheduler service instance"""
    global _scheduler_service
    _scheduler_service = service

def get_scheduler_service():
    """Get the scheduler service instance"""
    if _scheduler_service is None:
        raise HTTPException(status_code=503, detail="Scheduler service not available")
    return _scheduler_service

@router.get("/status")
async def get_scheduler_status():
    """Get the current status of the scheduler and all scheduled tasks"""
    try:
        scheduler_service = get_scheduler_service()
        status = scheduler_service.get_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting scheduler status: {e}")
        return {
            'success': False,
            'message': f'Failed to get scheduler status: {str(e)}'
        }

@router.post("/tasks/user-import/toggle")
async def toggle_user_import_schedule():
    """Toggle the user import schedule on/off"""
    try:
        scheduler_service = get_scheduler_service()
        result = await scheduler_service.toggle_user_import_schedule()
        return result
        
    except Exception as e:
        logger.error(f"❌ Error toggling user import schedule: {e}")
        return {
            'success': False,
            'message': f'Failed to toggle schedule: {str(e)}'
        }

@router.post("/tasks/user-import/run-now")
async def run_user_import_now():
    """Run user import immediately"""
    try:
        scheduler_service = get_scheduler_service()
        result = await scheduler_service.run_user_import_now()
        return result
        
    except Exception as e:
        logger.error(f"❌ Error running immediate user import: {e}")
        return {
            'success': False,
            'message': f'Failed to run import: {str(e)}'
        }

@router.get("/tasks")
async def list_scheduled_tasks():
    """List all scheduled tasks"""
    try:
        scheduler_service = get_scheduler_service()
        
        if not hasattr(scheduler_service, 'scheduler') or not scheduler_service.scheduler:
            return {
                'success': False,
                'message': 'Scheduler not initialized'
            }
            
        jobs = scheduler_service.scheduler.get_jobs()
        
        tasks = []
        for job in jobs:
            tasks.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'enabled': job.next_run_time is not None,
                'trigger': str(job.trigger)
            })
            
        return {
            'success': True,
            'data': {
                'tasks': tasks,
                'total_count': len(tasks)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing scheduled tasks: {e}")
        return {
            'success': False,
            'message': f'Failed to list tasks: {str(e)}'
        }

@router.get("/health")
async def scheduler_health():
    """Health check for the scheduler service"""
    try:
        scheduler_service = get_scheduler_service()
        
        return {
            'success': True,
            'data': {
                'scheduler_running': scheduler_service.is_running if hasattr(scheduler_service, 'is_running') else False,
                'status': 'healthy'
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking scheduler health: {e}")
        return {
            'success': False,
            'message': f'Scheduler health check failed: {str(e)}'
        }
