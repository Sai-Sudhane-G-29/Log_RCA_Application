"""
Router for log-related endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from mitra_ai_foundation.api.services.task_service import send_task_to_celery
from api.models.schemas import LogAnalysisRequest, ErrorAnalysisRequest
from mitra_ai_foundation.api.models.schemas import TaskResponse
from common.enum.task_types import LogTaskType

router = APIRouter(tags=["logs"])

@router.post("/analyze-logs", response_model=TaskResponse)
def analyze_logs(request: LogAnalysisRequest):
    """
    Submit logs for analysis.
    
    This endpoint sends a task to the Celery worker through Redis.
    """
    # Prepare the task data
    log_data = {
        "source": request.source,
        "logs": request.logs,
        "metadata": request.metadata
    }
    
    # Send the task to Celery
    task_id = send_task_to_celery(LogTaskType.PROCESS_LOGS, kwargs={"log_data": log_data})
    
    return TaskResponse(task_id=task_id)

@router.post("/analyze-errors", response_model=TaskResponse)
def analyze_errors(request: ErrorAnalysisRequest):
    """
    Analyze specific errors in logs.
    
    This endpoint sends a task to the Celery worker through Redis.
    """
    # Prepare the task data
    error_data = {
        "log_id": request.log_id,
        "error_type": request.error_type,
        "context_lines": request.context_lines
    }
    
    # Send the task to Celery
    task_id = send_task_to_celery(LogTaskType.ANALYZE_ERRORS, kwargs={"error_data": error_data})
    
    return TaskResponse(task_id=task_id)

@router.post("/generate-rca-report", response_model=TaskResponse)
def generate_rca_report(log_id: str):
    """
    Generate a root cause analysis report for a specific log.
    
    This endpoint sends a task to the Celery worker through Redis.
    """
    # Send the task to Celery
    task_id = send_task_to_celery(LogTaskType.GENERATE_RCA_REPORT, kwargs={"log_id": log_id})
    
    return TaskResponse(task_id=task_id)