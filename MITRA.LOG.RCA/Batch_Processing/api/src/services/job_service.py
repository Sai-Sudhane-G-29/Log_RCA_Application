"""
Job service for managing batch processing jobs
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from api.src.models.job import BatchJob, JobQueue, JobMetadata, JobStatus
from api.src.schemas.job import CreateJobRequest, JobResponse, JobStatusResponse
from api.src.core.logging import get_logger
from api.src.db.database import get_db_session

logger = get_logger(__name__)

class JobService:
    """Service for managing batch processing jobs"""
    
    def __init__(self):
        self.logger = logger
    
    async def create_job(self, job_request: CreateJobRequest) -> JobResponse:
        """Create a new batch processing job"""
        try:
            job_id = f"job_{uuid.uuid4().hex[:8]}"
            
            # Create job record
            job_data = {
                "job_id": job_id,
                "status": JobStatus.QUEUED,
                "job_type": job_request.job_type.value,
                "config": job_request.config.dict() if job_request.config else {},
                "log_files": job_request.log_files,
            }
            
            with next(get_db_session()) as db:
                # Create batch job
                batch_job = BatchJob(**job_data)
                db.add(batch_job)
                db.flush()
                
                # Add to job queue
                job_queue = JobQueue(
                    job_id=job_id,
                    priority=job_request.priority or 0
                )
                db.add(job_queue)
                
                # Create metadata record
                metadata = JobMetadata(
                    job_id=job_id,
                    source_files=job_request.log_files,
                )
                db.add(metadata)
                
                db.commit()
                db.refresh(batch_job)
                
                self.logger.info(f"Created job {job_id} with {len(job_request.log_files)} files")
                return JobResponse(**batch_job.to_dict())
                
        except Exception as e:
            self.logger.error(f"Error creating job: {str(e)}")
            raise
    
    async def get_job(self, job_id: str) -> Optional[JobResponse]:
        """Get job by ID"""
        try:
            with next(get_db_session()) as db:
                job = db.query(BatchJob).filter(BatchJob.job_id == job_id).first()
                if job:
                    return JobResponse(**job.to_dict())
                return None
        except Exception as e:
            self.logger.error(f"Error getting job {job_id}: {str(e)}")
            raise
    
    async def get_jobs(
        self, 
        status: Optional[JobStatus] = None,
        job_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[JobResponse]:
        """Get list of jobs with optional filtering"""
        try:
            with next(get_db_session()) as db:
                query = db.query(BatchJob)
                
                if status:
                    query = query.filter(BatchJob.status == status)
                if job_type:
                    query = query.filter(BatchJob.job_type == job_type)
                
                jobs = query.order_by(desc(BatchJob.created_at)).offset(offset).limit(limit).all()
                return [JobResponse(**job.to_dict()) for job in jobs]
        except Exception as e:
            self.logger.error(f"Error getting jobs: {str(e)}")
            raise
    
    async def update_job_status(
        self, 
        job_id: str, 
        status: JobStatus, 
        error_message: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update job status and related fields"""
        try:
            with next(get_db_session()) as db:
                job = db.query(BatchJob).filter(BatchJob.job_id == job_id).first()
                if not job:
                    return False
                
                job.status = status
                job.updated_at = datetime.utcnow()
                
                if status == JobStatus.RUNNING:
                    job.started_at = datetime.utcnow()
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    job.completed_at = datetime.utcnow()
                
                if error_message:
                    job.error_message = error_message
                
                if results:
                    job.results = results
                
                db.commit()
                self.logger.info(f"Updated job {job_id} status to {status.value}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating job {job_id} status: {str(e)}")
            raise
    
    async def update_job_progress(
        self, 
        job_id: str, 
        processed_records: int, 
        total_records: Optional[int] = None,
        failed_records: Optional[int] = None
    ) -> bool:
        """Update job progress metrics"""
        try:
            with next(get_db_session()) as db:
                job = db.query(BatchJob).filter(BatchJob.job_id == job_id).first()
                if not job:
                    return False
                
                job.processed_records = processed_records
                if total_records is not None:
                    job.total_records = total_records
                if failed_records is not None:
                    job.failed_records = failed_records
                
                job.updated_at = datetime.utcnow()
                db.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating job {job_id} progress: {str(e)}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """Get detailed job status"""
        try:
            with next(get_db_session()) as db:
                job = db.query(BatchJob).filter(BatchJob.job_id == job_id).first()
                if not job:
                    return None
                
                # Calculate progress percentage
                progress = 0.0
                if job.total_records and job.total_records > 0:
                    progress = (job.processed_records / job.total_records) * 100
                
                # Estimate completion time
                estimated_completion = None
                if job.status == JobStatus.RUNNING and progress > 0:
                    elapsed_time = (datetime.utcnow() - job.started_at).total_seconds()
                    if progress > 0:
                        total_estimated_time = (elapsed_time / progress) * 100
                        remaining_time = total_estimated_time - elapsed_time
                        estimated_completion = datetime.utcnow() + timedelta(seconds=remaining_time)
                
                # Create status message
                message = self._get_status_message(job)
                
                return JobStatusResponse(
                    job_id=job_id,
                    status=job.status,
                    progress=min(progress, 100.0),
                    message=message,
                    estimated_completion=estimated_completion
                )
                
        except Exception as e:
            self.logger.error(f"Error getting job {job_id} status: {str(e)}")
            raise
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        try:
            with next(get_db_session()) as db:
                job = db.query(BatchJob).filter(BatchJob.job_id == job_id).first()
                if not job:
                    return False
                
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    return False  # Cannot cancel completed jobs
                
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                
                # Remove from queue if still queued
                queue_item = db.query(JobQueue).filter(JobQueue.job_id == job_id).first()
                if queue_item:
                    db.delete(queue_item)
                
                db.commit()
                self.logger.info(f"Cancelled job {job_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error cancelling job {job_id}: {str(e)}")
            raise
    
    async def get_next_job(self) -> Optional[str]:
        """Get next job from queue based on priority"""
        try:
            with next(get_db_session()) as db:
                queue_item = (
                    db.query(JobQueue)
                    .order_by(desc(JobQueue.priority), JobQueue.queue_time)
                    .first()
                )
                
                if queue_item:
                    job_id = queue_item.job_id
                    db.delete(queue_item)
                    db.commit()
                    return job_id
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting next job: {str(e)}")
            raise
    
    async def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up old completed jobs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with next(get_db_session()) as db:
                # Delete old completed/failed jobs
                deleted_jobs = (
                    db.query(BatchJob)
                    .filter(
                        and_(
                            BatchJob.completed_at < cutoff_date,
                            or_(
                                BatchJob.status == JobStatus.COMPLETED,
                                BatchJob.status == JobStatus.FAILED,
                                BatchJob.status == JobStatus.CANCELLED
                            )
                        )
                    )
                    .delete()
                )
                
                # Delete associated metadata
                db.query(JobMetadata).filter(
                    JobMetadata.created_at < cutoff_date
                ).delete()
                
                db.commit()
                self.logger.info(f"Cleaned up {deleted_jobs} old jobs")
                return deleted_jobs
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old jobs: {str(e)}")
            raise
    
    def _get_status_message(self, job: BatchJob) -> str:
        """Generate status message based on job state"""
        if job.status == JobStatus.QUEUED:
            return "Job is queued and waiting to be processed"
        elif job.status == JobStatus.RUNNING:
            if job.total_records > 0:
                return f"Processing records: {job.processed_records}/{job.total_records}"
            else:
                return "Job is currently running"
        elif job.status == JobStatus.COMPLETED:
            return f"Job completed successfully. Processed {job.processed_records} records"
        elif job.status == JobStatus.FAILED:
            return f"Job failed: {job.error_message}" if job.error_message else "Job failed"
        elif job.status == JobStatus.CANCELLED:
            return "Job was cancelled"
        else:
            return "Unknown status"

# Global job service instance
job_service = JobService()
