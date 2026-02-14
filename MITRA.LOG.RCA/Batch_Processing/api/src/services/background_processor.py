"""
Background processor for handling queued jobs
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

from api.src.core.config import settings
from api.src.core.logging import get_logger
from api.src.services.job_service import job_service
from api.src.services.spark_service import spark_service
from api.src.models.job import JobStatus

logger = get_logger(__name__)

class BackgroundProcessor:
    """Background processor for managing job execution"""
    
    def __init__(self):
        self.logger = logger
        self.is_running = False
        self._stop_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_JOBS)
        self._active_jobs: Dict[str, asyncio.Task] = {}
        self._processing_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background processor"""
        if self.is_running:
            return
        
        self.is_running = True
        self._stop_event.clear()
        
        # Start the main processing loop
        self._processing_task = asyncio.create_task(self._process_jobs_loop())
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Background processor started")
    
    async def stop(self):
        """Stop the background processor"""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_event.set()
        
        # Cancel active jobs
        for job_id, task in self._active_jobs.items():
            task.cancel()
            self.logger.info(f"Cancelled active job {job_id}")
        
        # Wait for processing task to complete
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        self.logger.info("Background processor stopped")
    
    async def _process_jobs_loop(self):
        """Main job processing loop"""
        while self.is_running:
            try:
                # Check if we can process more jobs
                if len(self._active_jobs) < settings.MAX_CONCURRENT_JOBS:
                    # Get next job from queue
                    next_job_id = await job_service.get_next_job()
                    
                    if next_job_id:
                        # Start processing the job
                        task = asyncio.create_task(self._process_job(next_job_id))
                        self._active_jobs[next_job_id] = task
                        
                        # Set up task completion callback
                        task.add_done_callback(
                            lambda t, job_id=next_job_id: self._on_job_complete(job_id, t)
                        )
                        
                        self.logger.info(f"Started processing job {next_job_id}")
                
                # Clean up completed tasks
                await self._cleanup_completed_tasks()
                
                # Wait before next iteration
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in job processing loop: {str(e)}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _process_job(self, job_id: str):
        """Process a single job"""
        try:
            # Get job details
            job = await job_service.get_job(job_id)
            if not job:
                self.logger.error(f"Job {job_id} not found")
                return
            
            self.logger.info(f"Processing job {job_id} of type {job.job_type}")
            
            # Process based on job type
            if job.job_type == "log_etl":
                await self._process_log_etl_job(job_id, job.log_files or [], job.config or {})
            elif job.job_type == "data_migration":
                await self._process_data_migration_job(job_id, job.config or {})
            else:
                await self._process_custom_job(job_id, job.config or {})
            
        except Exception as e:
            self.logger.error(f"Error processing job {job_id}: {str(e)}")
            await job_service.update_job_status(
                job_id, 
                JobStatus.FAILED, 
                error_message=str(e)
            )
    
    async def _process_log_etl_job(
        self, 
        job_id: str, 
        log_files: list, 
        config: Dict[str, Any]
    ):
        """Process log ETL job using Spark"""
        try:
            # Use thread pool for Spark processing (since Spark is blocking)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                lambda: asyncio.run(
                    spark_service.process_log_files(job_id, log_files, config)
                )
            )
            
            self.logger.info(f"Log ETL job {job_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Log ETL job {job_id} failed: {str(e)}")
            raise
    
    async def _process_data_migration_job(self, job_id: str, config: Dict[str, Any]):
        """Process data migration job"""
        try:
            await job_service.update_job_status(job_id, JobStatus.RUNNING)
            
            # Simulate data migration process
            total_steps = config.get("steps", 5)
            for step in range(total_steps):
                await asyncio.sleep(2)  # Simulate work
                await job_service.update_job_progress(
                    job_id,
                    processed_records=step + 1,
                    total_records=total_steps
                )
            
            await job_service.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                results={"migrated_records": total_steps * 100}
            )
            
            self.logger.info(f"Data migration job {job_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Data migration job {job_id} failed: {str(e)}")
            raise
    
    async def _process_custom_job(self, job_id: str, config: Dict[str, Any]):
        """Process custom job"""
        try:
            await job_service.update_job_status(job_id, JobStatus.RUNNING)
            
            # Simulate custom processing
            processing_time = config.get("processing_time", 10)  # seconds
            await asyncio.sleep(processing_time)
            
            await job_service.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                results={"custom_result": "success"}
            )
            
            self.logger.info(f"Custom job {job_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Custom job {job_id} failed: {str(e)}")
            raise
    
    def _on_job_complete(self, job_id: str, task: asyncio.Task):
        """Callback when job completes"""
        try:
            if task.cancelled():
                self.logger.info(f"Job {job_id} was cancelled")
            elif task.exception():
                self.logger.error(f"Job {job_id} failed with exception: {task.exception()}")
            else:
                self.logger.info(f"Job {job_id} completed successfully")
        except Exception as e:
            self.logger.error(f"Error in job completion callback: {str(e)}")
    
    async def _cleanup_completed_tasks(self):
        """Clean up completed tasks"""
        completed_jobs = []
        for job_id, task in self._active_jobs.items():
            if task.done():
                completed_jobs.append(job_id)
        
        for job_id in completed_jobs:
            del self._active_jobs[job_id]
    
    async def _cleanup_loop(self):
        """Periodic cleanup of old jobs and resources"""
        while self.is_running:
            try:
                await asyncio.sleep(settings.CLEANUP_INTERVAL)
                
                # Clean up old jobs
                deleted_count = await job_service.cleanup_old_jobs(days=30)
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old jobs")
                
                # Clean up Spark sessions if needed
                if len(self._active_jobs) == 0:
                    spark_service.close_spark_session()
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}")
    
    def get_active_jobs(self) -> Dict[str, str]:
        """Get list of currently active jobs"""
        return {
            job_id: "running" if not task.done() else "completed"
            for job_id, task in self._active_jobs.items()
        }
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel an active job"""
        if job_id in self._active_jobs:
            task = self._active_jobs[job_id]
            task.cancel()
            await job_service.update_job_status(job_id, JobStatus.CANCELLED)
            self.logger.info(f"Cancelled job {job_id}")
            return True
        return False

# Global background processor instance
background_processor = BackgroundProcessor()
