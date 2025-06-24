"""
OCS Portal - Scheduler Service
Manages automated tasks including user import scheduling
"""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for managing scheduled tasks in OCS Portal"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self.user_import_enabled = False
        
        # Configure scheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='America/Chicago'
        )
        
    async def start(self):
        """Start the scheduler service"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self.is_running = True
                logger.info("✅ Scheduler service started successfully")
                
                # Set up default user import schedule (daily at 6 AM)
                await self.setup_default_schedules()
                
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler service: {e}")
            raise
            
    async def stop(self):
        """Stop the scheduler service"""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                logger.info("✅ Scheduler service stopped")
        except Exception as e:
            logger.error(f"❌ Failed to stop scheduler service: {e}")
            
    async def setup_default_schedules(self):
        """Set up default scheduled tasks"""
        try:
            # Add user import job (disabled by default)
            if not self.scheduler.get_job('user_import_job'):
                self.scheduler.add_job(
                    func=self.run_user_import,
                    trigger=CronTrigger(hour=6, minute=0),  # Daily at 6 AM
                    id='user_import_job',
                    name='Daily User Import',
                    replace_existing=True
                )
                # Pause the job initially
                self.scheduler.pause_job('user_import_job')
                logger.info("📅 User import job scheduled (initially disabled)")
                
        except Exception as e:
            logger.error(f"❌ Failed to setup default schedules: {e}")
            
    async def run_user_import(self):
        """Execute the user import process"""
        try:
            logger.info("🔄 Starting scheduled user import...")
            
            # Import the user import service here to avoid circular imports
            from user_import_service import UserImportService
            from database import get_db_connection
            
            # Get database connection
            db = next(get_db_connection())
            
            try:
                # Create user import service instance
                import_service = UserImportService(db)
                
                # Run the import (this should be an async method)
                result = await import_service.run_scheduled_import()
                
                if result.get('success', False):
                    logger.info(f"✅ Scheduled user import completed: {result.get('message', 'Success')}")
                else:
                    logger.error(f"❌ Scheduled user import failed: {result.get('message', 'Unknown error')}")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error during scheduled user import: {e}")
            
    async def toggle_user_import_schedule(self) -> Dict[str, Any]:
        """Toggle the user import schedule on/off"""
        try:
            job = self.scheduler.get_job('user_import_job')
            if not job:
                return {
                    'success': False,
                    'message': 'User import job not found'
                }
                
            if self.user_import_enabled:
                # Disable the schedule
                self.scheduler.pause_job('user_import_job')
                self.user_import_enabled = False
                message = 'User import schedule disabled'
                logger.info(f"⏸️ {message}")
            else:
                # Enable the schedule
                self.scheduler.resume_job('user_import_job')
                self.user_import_enabled = True
                message = 'User import schedule enabled'
                logger.info(f"▶️ {message}")
                
            return {
                'success': True,
                'message': message,
                'enabled': self.user_import_enabled
            }
            
        except Exception as e:
            logger.error(f"❌ Error toggling user import schedule: {e}")
            return {
                'success': False,
                'message': f'Failed to toggle schedule: {str(e)}'
            }
            
    async def run_user_import_now(self) -> Dict[str, Any]:
        """Run user import immediately"""
        try:
            logger.info("🚀 Running user import immediately...")
            
            # Run the import in a background task
            asyncio.create_task(self.run_user_import())
            
            return {
                'success': True,
                'message': 'User import started successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error running immediate user import: {e}")
            return {
                'success': False,
                'message': f'Failed to start import: {str(e)}'
            }
            
    def get_status(self) -> Dict[str, Any]:
        """Get the current scheduler status"""
        try:
            job = self.scheduler.get_job('user_import_job') if self.scheduler else None
            
            next_run = None
            if job and not job.next_run_time:
                # Job is paused
                next_run = None
            elif job:
                next_run = job.next_run_time.isoformat() if job.next_run_time else None
                
            return {
                'success': True,
                'data': {
                    'scheduler_running': self.is_running,
                    'user_import_enabled': self.user_import_enabled,
                    'next_run': next_run,
                    'jobs_count': len(self.scheduler.get_jobs()) if self.scheduler else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting scheduler status: {e}")
            return {
                'success': False,
                'message': f'Failed to get status: {str(e)}'
            }
