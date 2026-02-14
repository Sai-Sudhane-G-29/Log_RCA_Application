"""
API routes for batch job management
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
import uuid

from api.src.schemas.job import (
    CreateJobRequest,
    JobResponse,
    JobStatusResponse,
    JobListResponse,
    SuccessResponse,
    ErrorResponse,
    JobStatusEnum
)
from api.src.services.job_service import job_service
from api.src.services.background_processor import background_processor
from api.src.models.job import JobStatus
from api.src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/jobs", response_model=JobResponse)
async def create_batch_job(job_request: CreateJobRequest):
    """
    Create a new batch processing job
    
    - **job_type**: Type of job (log_etl, data_migration, custom)
    - **log_files**: List of log file paths to process
    - **config**: Job configuration parameters
    - **priority**: Job priority (0-10)
    """
    try:
        job = await job_service.create_job(job_request)
        logger.info(f"Created job {job.job_id}")
        return job
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs", response_model=JobListResponse)
async def get_jobs(
    status: Optional[JobStatusEnum] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(100, ge=1, le=1000, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip")
):
    """
    Get list of batch processing jobs with optional filtering
    """
    try:
        # Convert enum to model enum if provided
        status_filter = None
        if status:
            status_filter = JobStatus(status.value)
        
        jobs = await job_service.get_jobs(
            status=status_filter,
            job_type=job_type,
            limit=limit,
            offset=offset
        )
        
        # Calculate pagination info
        total_jobs = len(jobs)  # In a real app, you'd get this from a separate count query
        total_pages = (total_jobs + limit - 1) // limit
        page = (offset // limit) + 1
        
        return JobListResponse(
            jobs=jobs,
            total=total_jobs,
            page=page,
            page_size=limit,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str = Path(..., description="Job ID")
):
    """
    Get details of a specific batch processing job
    """
    try:
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str = Path(..., description="Job ID")
):
    """
    Get detailed status of a specific batch processing job
    """
    try:
        status = await job_service.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/cancel", response_model=SuccessResponse)
async def cancel_job(
    job_id: str = Path(..., description="Job ID")
):
    """
    Cancel a batch processing job
    """
    try:
        # Try to cancel in background processor first
        cancelled_in_processor = await background_processor.cancel_job(job_id)
        
        # Update job status in database
        success = await job_service.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found or cannot be cancelled")
        
        message = "Job cancelled successfully"
        if cancelled_in_processor:
            message += " (was actively running)"
        
        logger.info(f"Cancelled job {job_id}")
        return SuccessResponse(
            message=message,
            data={"job_id": job_id, "cancelled_in_processor": cancelled_in_processor}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}", response_model=SuccessResponse)
async def delete_job(
    job_id: str = Path(..., description="Job ID")
):
    """
    Delete a batch processing job (only completed, failed, or cancelled jobs)
    """
    try:
        # First check if job exists and is in a deletable state
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        if job.status not in [JobStatusEnum.COMPLETED, JobStatusEnum.FAILED, JobStatusEnum.CANCELLED]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete job in status {job.status}. Only completed, failed, or cancelled jobs can be deleted."
            )
        
        # TODO: Implement job deletion logic
        # This would involve deleting from database and cleaning up any associated files
        
        logger.info(f"Deleted job {job_id}")
        return SuccessResponse(
            message="Job deleted successfully",
            data={"job_id": job_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/logs")
async def get_job_logs(
    job_id: str = Path(..., description="Job ID"),
    lines: int = Query(100, ge=1, le=1000, description="Number of log lines to return")
):
    """
    Get logs for a specific job
    """
    try:
        # TODO: Implement log retrieval logic
        # This would read from job-specific log files
        
        # Mock response for now
        return {
            "job_id": job_id,
            "logs": [
                f"[2024-01-01 10:00:00] INFO: Job {job_id} started",
                f"[2024-01-01 10:00:01] INFO: Processing file 1 of 3",
                f"[2024-01-01 10:00:05] INFO: Processed 1000 records",
                f"[2024-01-01 10:01:00] INFO: Job {job_id} completed"
            ],
            "total_lines": 4,
            "requested_lines": lines
        }
    except Exception as e:
        logger.error(f"Error getting logs for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str = Path(..., description="Job ID")
):
    """
    Retry a failed batch processing job
    """
    try:
        # Get the original job
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        if job.status != JobStatusEnum.FAILED:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot retry job in status {job.status}. Only failed jobs can be retried."
            )
        
        # Create a new job with the same configuration
        retry_request = CreateJobRequest(
            job_type=job.job_type,
            log_files=job.log_files or [],
            config=job.config,
            priority=5  # Higher priority for retries
        )
        
        new_job = await job_service.create_job(retry_request)
        
        logger.info(f"Created retry job {new_job.job_id} for original job {job_id}")
        return new_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
