"""
API routes for system status and monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta

from api.src.services.background_processor import background_processor
from api.src.services.job_service import job_service
from api.src.services.spark_service import spark_service
from api.src.models.job import JobStatus
from api.src.core.config import settings
from api.src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/status")
async def get_system_status():
    """
    Get overall system status and health
    """
    try:
        # Get active jobs from background processor
        active_jobs = background_processor.get_active_jobs()
        
        # Get job statistics
        running_jobs = await job_service.get_jobs(status=JobStatus.RUNNING, limit=1000)
        queued_jobs = await job_service.get_jobs(status=JobStatus.QUEUED, limit=1000)
        
        # System metrics
        system_status = {
            "system": {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            },
            "background_processor": {
                "status": "running" if background_processor.is_running else "stopped",
                "active_jobs": len(active_jobs),
                "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS
            },
            "job_queue": {
                "queued_jobs": len(queued_jobs),
                "running_jobs": len(running_jobs),
                "active_job_ids": list(active_jobs.keys())
            },
            "spark": {
                "status": "available",
                "master": settings.SPARK_MASTER,
                "app_name": settings.SPARK_APP_NAME
            },
            "configuration": {
                "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
                "job_timeout": settings.JOB_TIMEOUT,
                "cleanup_interval": settings.CLEANUP_INTERVAL
            }
        }
        
        return system_status
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_system_metrics():
    """
    Get detailed system metrics and statistics
    """
    try:
        # Get job statistics for the last 24 hours
        from datetime import datetime, timedelta
        
        # This would typically query the database for metrics
        # For now, return mock metrics
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "time_period": "last_24_hours",
            "job_statistics": {
                "total_jobs": 150,
                "completed_jobs": 142,
                "failed_jobs": 5,
                "cancelled_jobs": 2,
                "running_jobs": 1,
                "queued_jobs": 0
            },
            "processing_metrics": {
                "total_records_processed": 1500000,
                "average_processing_time": 320,  # seconds
                "total_processing_time": 45600,  # seconds
                "throughput": {
                    "records_per_second": 328.95,
                    "jobs_per_hour": 6.25
                }
            },
            "resource_usage": {
                "peak_memory_usage": 2048,  # MB
                "average_cpu_usage": 65,  # percentage
                "disk_usage": {
                    "logs": "1.2GB",
                    "temp_files": "500MB",
                    "processed_data": "15GB"
                }
            },
            "error_statistics": {
                "common_errors": [
                    {"error": "FileNotFound", "count": 3},
                    {"error": "ParseError", "count": 2}
                ],
                "retry_success_rate": 80.0
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Simple health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "batch_processing_engine"
    }

@router.get("/stats/jobs")
async def get_job_statistics():
    """
    Get job-related statistics
    """
    try:
        # Get jobs by status
        completed_jobs = await job_service.get_jobs(status=JobStatus.COMPLETED, limit=1000)
        failed_jobs = await job_service.get_jobs(status=JobStatus.FAILED, limit=1000)
        running_jobs = await job_service.get_jobs(status=JobStatus.RUNNING, limit=1000)
        queued_jobs = await job_service.get_jobs(status=JobStatus.QUEUED, limit=1000)
        cancelled_jobs = await job_service.get_jobs(status=JobStatus.CANCELLED, limit=1000)
        
        # Calculate success rate
        total_completed = len(completed_jobs) + len(failed_jobs) + len(cancelled_jobs)
        success_rate = (len(completed_jobs) / total_completed * 100) if total_completed > 0 else 0
        
        statistics = {
            "job_counts": {
                "completed": len(completed_jobs),
                "failed": len(failed_jobs),
                "running": len(running_jobs),
                "queued": len(queued_jobs),
                "cancelled": len(cancelled_jobs),
                "total": total_completed + len(running_jobs) + len(queued_jobs)
            },
            "success_rate": round(success_rate, 2),
            "failure_rate": round((len(failed_jobs) / total_completed * 100) if total_completed > 0 else 0, 2),
            "active_processing": {
                "running": len(running_jobs),
                "queued": len(queued_jobs),
                "capacity_utilization": (len(running_jobs) / settings.MAX_CONCURRENT_JOBS * 100)
            }
        }
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting job statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/performance")
async def get_performance_statistics():
    """
    Get performance-related statistics
    """
    try:
        # This would typically aggregate data from job metadata
        # For now, return mock performance data
        
        performance = {
            "timestamp": datetime.utcnow().isoformat(),
            "average_metrics": {
                "job_duration": 298,  # seconds
                "records_per_job": 10000,
                "throughput": 33.6,  # records per second
                "memory_usage": 512,  # MB
                "cpu_usage": 68  # percentage
            },
            "trending": {
                "last_hour": {
                    "jobs_completed": 12,
                    "average_duration": 245,
                    "success_rate": 91.7
                },
                "last_day": {
                    "jobs_completed": 156,
                    "average_duration": 298,
                    "success_rate": 94.2
                }
            },
            "peak_performance": {
                "highest_throughput": 125.5,  # records per second
                "fastest_job": 45,  # seconds
                "largest_job": 250000  # records
            }
        }
        
        return performance
        
    except Exception as e:
        logger.error(f"Error getting performance statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/cleanup")
async def trigger_cleanup():
    """
    Manually trigger cleanup of old jobs and temporary files
    """
    try:
        # Clean up old jobs
        deleted_jobs = await job_service.cleanup_old_jobs(days=7)  # Clean jobs older than 7 days
        
        # Close unused Spark sessions
        spark_service.close_spark_session()
        
        return {
            "status": "success",
            "message": "Cleanup completed",
            "details": {
                "deleted_jobs": deleted_jobs,
                "spark_sessions_closed": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/config")
async def get_configuration():
    """
    Get current system configuration
    """
    try:
        config = {
            "application": {
                "name": settings.APP_NAME,
                "version": settings.VERSION,
                "debug": settings.DEBUG,
                "host": settings.HOST,
                "port": settings.PORT
            },
            "processing": {
                "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS,
                "job_timeout": settings.JOB_TIMEOUT,
                "batch_size": settings.BATCH_SIZE,
                "max_retries": settings.MAX_RETRIES,
                "retry_delay": settings.RETRY_DELAY
            },
            "spark": {
                "master": settings.SPARK_MASTER,
                "app_name": settings.SPARK_APP_NAME,
                "driver_memory": settings.SPARK_DRIVER_MEMORY,
                "executor_memory": settings.SPARK_EXECUTOR_MEMORY
            },
            "storage": {
                "log_files_path": settings.LOG_FILES_PATH,
                "processed_files_path": settings.PROCESSED_FILES_PATH
            },
            "monitoring": {
                "status_check_interval": settings.STATUS_CHECK_INTERVAL,
                "cleanup_interval": settings.CLEANUP_INTERVAL
            }
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
