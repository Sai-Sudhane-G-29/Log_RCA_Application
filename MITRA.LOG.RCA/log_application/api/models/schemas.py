from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum

class LogTaskType(str, Enum):
    """Enumeration of log analysis task types."""
    PROCESS_LOGS = "process_logs"
    ANALYZE_ERRORS = "analyze_errors"
    GENERATE_RCA_REPORT = "generate_rca_report"
    PATTERN_ANALYSIS = "pattern_analysis"
    ANOMALY_DETECTION = "anomaly_detection"

class LogAnalysisRequest(BaseModel):
    """Request model for log analysis."""
    source: str = Field(..., description="Source of the logs (e.g., 'application', 'system', 'network')")
    logs: List[str] = Field(..., description="List of log entries to analyze")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata about the logs"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "source": "application",
                "logs": [
                    "2023-01-01 10:00:00 ERROR Database connection failed",
                    "2023-01-01 10:00:01 WARN Retrying connection...",
                    "2023-01-01 10:00:02 INFO Connection established"
                ],
                "metadata": {
                    "environment": "production",
                    "application": "user-service"
                }
            }
        }

class ErrorAnalysisRequest(BaseModel):
    """Request model for error analysis."""
    log_id: str = Field(..., description="ID of the log to analyze")
    error_type: Optional[str] = Field(
        None,
        description="Specific error type to focus on (e.g., 'DatabaseError', 'TimeoutError')"
    )
    context_lines: int = Field(
        5,
        description="Number of context lines to include around the error",
        ge=1,
        le=20
    )
    
    class Config:
        schema_extra = {
            "example": {
                "log_id": "log_12345",
                "error_type": "DatabaseConnectionError",
                "context_lines": 5
            }
        }

class TaskResponse(BaseModel):
    """Response model for task submission."""
    task_id: str = Field(..., description="ID of the submitted task")
    status: str = Field("submitted", description="Initial status of the task")
    message: str = Field("Task submitted successfully", description="Status message")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "status": "submitted",
                "message": "Task submitted successfully"
            }
        }

class RCAReportRequest(BaseModel):
    """Request model for RCA report generation."""
    log_id: str = Field(..., description="ID of the log to generate RCA report for")
    timeframe_hours: Optional[int] = Field(
        24,
        description="Timeframe in hours to consider for root cause analysis",
        ge=1,
        le=168  # 1 week
    )
    include_suggestions: bool = Field(
        True,
        description="Whether to include remediation suggestions in the report"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "log_id": "log_12345",
                "timeframe_hours": 24,
                "include_suggestions": True
            }
        }