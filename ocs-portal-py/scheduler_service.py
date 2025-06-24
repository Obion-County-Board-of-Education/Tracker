"""
OCS Portal - Scheduler Service
Manages automated tasks including user import scheduling with execution tracking
"""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import logging
from typing import Optional, Dict, Any, List
import uuid
import json
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for managing scheduled tasks in OCS Portal with execution tracking"""
    
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
            
    def _log_execution_start(self, task_name: str, task_type: str = 'user_import', executed_by: str = 'scheduler') -> Optional[str]:
        """Log the start of a task execution"""
        try:
            from database import get_db
            from ocs_shared_models.timezone_utils import central_now
            
            db = next(get_db())
            execution_id = str(uuid.uuid4())
            
            # Insert execution record
            db.execute(text("""
                INSERT INTO task_executions 
                (id, task_name, task_type, status, started_at, executed_by)
                VALUES (:id, :task_name, :task_type, 'running', :started_at, :executed_by)
            """), {
                'id': execution_id,
                'task_name': task_name,
                'task_type': task_type,
                'started_at': central_now(),
                'executed_by': executed_by
            })
            db.commit()
            db.close()
            
            logger.info(f"📝 Logged execution start: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"❌ Error logging execution start: {e}")
            return None
    
    def _log_execution_complete(self, execution_id: str, status: str, result_data: Dict = None, error_message: str = None):
        """Log the completion of a task execution"""
        try:
            if not execution_id:
                return
                
            from database import get_db
            from ocs_shared_models.timezone_utils import central_now
            
            db = next(get_db())
            completed_at = central_now()
            
            # Get the start time to calculate duration
            start_result = db.execute(text("""
                SELECT started_at FROM task_executions WHERE id = :id
            """), {'id': execution_id}).fetchone()
            
            duration_seconds = 0
            if start_result:
                start_time = start_result[0]
                duration_seconds = int((completed_at - start_time).total_seconds())
            
            # Update execution record
            db.execute(text("""
                UPDATE task_executions 
                SET status = :status, completed_at = :completed_at, 
                    duration_seconds = :duration, result_data = :result_data,
                    error_message = :error_message
                WHERE id = :id
            """), {
                'id': execution_id,
                'status': status,
                'completed_at': completed_at,
                'duration': duration_seconds,
                'result_data': json.dumps(result_data) if result_data else None,
                'error_message': error_message
            })
            db.commit()
            db.close()
            
            logger.info(f"📝 Logged execution complete: {execution_id} - {status}")
            
        except Exception as e:
            logger.error(f"❌ Error logging execution completion: {e}")
            
    async def run_user_import(self):
        """Execute the user import process with execution tracking"""
        execution_id = None
        try:
            logger.info("🔄 Starting scheduled user import...")
            
            # Log execution start
            execution_id = self._log_execution_start("Scheduled User Import", "user_import", "scheduler")            # Import the user import service here to avoid circular imports            from user_import_service import UserImportService
            from database import get_db_session
            
            # Get database connection
            with get_db_session() as db:
                # Create user import service instance
                import_service = UserImportService(db)
                  # Run the import (this should be an async method)
                result = await import_service.run_scheduled_import()
                  # Check if import completed successfully or with non-critical errors
                success = result.get('success', False)
                message = result.get('message', '')
                has_errors = len(result.get('errors', [])) > 0
                
                # Consider it successful if:
                # 1. success = True, OR
                # 2. message contains "completed" (even with errors), OR  
                # 3. message contains "imported" or "updated"
                is_successful = (success or 
                               'completed' in message.lower() or 
                               'imported' in message.lower() or
                               'updated' in message.lower())
                
                if is_successful:
                    # Import completed successfully (with or without warnings)
                    if has_errors or 'error' in message.lower() or 'warning' in message.lower():
                        logger.warning(f"⚠️ Scheduled user import completed with warnings: {message}")
                        self._log_execution_complete(execution_id, 'completed_with_warnings', result)
                    else:
                        logger.info(f"✅ Scheduled user import completed: {message}")
                        self._log_execution_complete(execution_id, 'completed', result)
                else:
                    logger.error(f"❌ Scheduled user import failed: {message}")
                    self._log_execution_complete(execution_id, 'failed', result, message)
                    
        except Exception as e:
            logger.error(f"❌ Error during scheduled user import: {e}")
            self._log_execution_complete(execution_id, 'failed', None, str(e))
            
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
        """Run user import immediately with execution tracking"""
        execution_id = None
        try:
            logger.info("🚀 Running user import immediately...")
            
            # Log execution start
            execution_id = self._log_execution_start("Manual User Import", "user_import", "manual")
            
            # Run the import in a background task with execution tracking
            asyncio.create_task(self._run_manual_import(execution_id))
            
            return {
                'success': True,
                'message': 'User import started successfully',
                'execution_id': execution_id
            }
            
        except Exception as e:
            logger.error(f"❌ Error running immediate user import: {e}")
            self._log_execution_complete(execution_id, 'failed', None, str(e))
            return {
                'success': False,                'message': f'Failed to start import: {str(e)}'
            }
    
    async def _run_manual_import(self, execution_id: str):
        """Run manual import in background with execution tracking"""
        try:
            # Import user import service
            from user_import_service import UserImportService
            from database import get_db_session
            
            # Get database connection
            with get_db_session() as db:
                # Create user import service instance
                import_service = UserImportService(db)
                  # Run the import
                result = await import_service.run_scheduled_import()
                  # Check if import completed successfully or with non-critical errors
                success = result.get('success', False)
                message = result.get('message', '')
                has_errors = len(result.get('errors', [])) > 0
                
                # Consider it successful if:
                # 1. success = True, OR
                # 2. message contains "completed" (even with errors), OR  
                # 3. message contains "imported" or "updated"
                is_successful = (success or 
                               'completed' in message.lower() or 
                               'imported' in message.lower() or
                               'updated' in message.lower())
                
                if is_successful:
                    # Import completed successfully (with or without warnings)
                    if has_errors or 'error' in message.lower() or 'warning' in message.lower():
                        logger.warning(f"⚠️ Manual user import completed with warnings: {message}")
                        self._log_execution_complete(execution_id, 'completed_with_warnings', result)
                    else:
                        logger.info(f"✅ Manual user import completed: {message}")
                        self._log_execution_complete(execution_id, 'completed', result)
                else:
                    logger.error(f"❌ Manual user import failed: {message}")
                    self._log_execution_complete(execution_id, 'failed', result, message)
                    
        except Exception as e:
            logger.error(f"❌ Error during manual user import: {e}")
            self._log_execution_complete(execution_id, 'failed', None, str(e))
            
    def get_status(self) -> Dict[str, Any]:
        """Get the current scheduler status with recent executions"""
        try:
            job = self.scheduler.get_job('user_import_job') if self.scheduler else None

            next_run = None
            if job and not job.next_run_time:
                # Job is paused
                next_run = None
            elif job:
                next_run = job.next_run_time.isoformat() if job.next_run_time else None

            # Get recent executions from database
            recent_executions = self._get_recent_executions()

            return {
                'success': True,
                'data': {
                    'scheduler_running': self.is_running,
                    'user_import_enabled': self.user_import_enabled,
                    'next_run': next_run,
                    'jobs_count': len(self.scheduler.get_jobs()) if self.scheduler else 0,
                    'recent_executions': recent_executions
                }
            }

        except Exception as e:
            logger.error(f"❌ Error getting scheduler status: {e}")
            return {
                'success': False,
                'message': f'Failed to get status: {str(e)}'
            }
    
    def _get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task executions from database"""
        try:
            from database import get_db
            from ocs_shared_models.timezone_utils import format_central_time
            
            db = next(get_db())
            
            result = db.execute(text("""
                SELECT id, task_name, task_type, status, started_at, completed_at, 
                       duration_seconds, executed_by, error_message, result_data
                FROM task_executions 
                ORDER BY started_at DESC 
                LIMIT :limit
            """), {'limit': limit}).fetchall()
            
            executions = []
            for row in result:
                execution = {
                    'id': row[0],
                    'task_name': row[1],
                    'task_type': row[2],
                    'status': row[3],
                    'started_at': format_central_time(row[4]) if row[4] else None,
                    'completed_at': format_central_time(row[5]) if row[5] else None,
                    'duration_seconds': row[6],
                    'executed_by': row[7],
                    'error_message': row[8],
                    'result_summary': self._format_result_summary(row[9])
                }
                executions.append(execution)
            
            db.close()
            return executions
            
        except Exception as e:
            logger.error(f"❌ Error getting recent executions: {e}")
            return []
    
    def _format_result_summary(self, result_data: str) -> str:
        """Format execution result data into a readable summary"""
        try:
            if not result_data:
                return "No details available"
            
            if isinstance(result_data, str):
                data = json.loads(result_data)
            else:
                data = result_data
            
            if isinstance(data, dict):
                # Format user import results
                if 'staff_updated' in data or 'students_updated' in data:
                    staff_new = data.get('staff_new', 0)
                    staff_updated = data.get('staff_updated', 0)
                    students_new = data.get('students_new', 0)
                    students_updated = data.get('students_updated', 0)
                    errors = data.get('total_errors', 0)
                    
                    summary_parts = []
                    if staff_new > 0:
                        summary_parts.append(f"{staff_new} new staff")
                    if staff_updated > 0:
                        summary_parts.append(f"{staff_updated} staff updated")
                    if students_new > 0:
                        summary_parts.append(f"{students_new} new students")
                    if students_updated > 0:
                        summary_parts.append(f"{students_updated} students updated")
                    if errors > 0:
                        summary_parts.append(f"{errors} errors")
                    
                    return ", ".join(summary_parts) if summary_parts else "No changes"
                else:
                    return str(data)
            else:
                return str(data)
                
        except Exception as e:
            logger.error(f"❌ Error formatting result summary: {e}")
            return "Error formatting results"