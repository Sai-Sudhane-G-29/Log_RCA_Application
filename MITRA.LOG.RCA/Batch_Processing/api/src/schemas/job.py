"""
Pydantic schemas for request/response models
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class JobStatusEnum(str, Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobTypeEnum(str, Enum):
    """Job type enumeration"""
    LOG_ETL = "log_etl"
    DATA_MIGRATION = "data_migration"
    CUSTOM = "custom"

class JobConfigSchema(BaseModel):
    """Job configuration schema"""
    log_format: Optional[str] = "default"
    parse_rules: Optional[Dict[str, Any]] = {}
    transformations: Optional[List[Dict[str, Any]]] = []
    output_format: Optional[str] = "parquet"
    partition_by: Optional[List[str]] = []
    
    class Config:
        schema_extra = {
            "example": {
                "log_format": "apache_common",
                "parse_rules": {
                    "timestamp_format": "%Y-%m-%d %H:%M:%S",
                    "delimiter": " "
                },
                "transformations": [
                    {
                        "type": "filter",
                        "condition": "status_code >= 400"
                    }
                ],
                "output_format": "parquet",
                "partition_by": ["date", "status_code"]
            }
        }

class CreateJobRequest(BaseModel):
    """Create job request schema"""
    job_type: JobTypeEnum = JobTypeEnum.LOG_ETL
    log_files: List[str] = Field(..., description="List of log file paths to process")
    config: Optional[JobConfigSchema] = None
    priority: Optional[int] = Field(0, ge=0, le=10, description="Job priority (0-10)")
    
    @validator("log_files")
    def validate_log_files(cls, v):
        if not v:
            raise ValueError("At least one log file must be provided")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "job_type": "log_etl",
                "log_files": ["/var/log/app.log", "/var/log/error.log"],
                "config": {
                    "log_format": "json",
                    "transformations": []
                },
                "priority": 5
            }
        }

class JobResponse(BaseModel):
    """Job response schema"""
    id: int
    job_id: str
    status: JobStatusEnum
    job_type: str
    config: Optional[Dict[str, Any]] = None
    log_files: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    total_records: Optional[int] = 0
    processed_records: Optional[int] = 0
    failed_records: Optional[int] = 0
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class JobStatusResponse(BaseModel):
    """Job status response schema"""
    job_id: str
    status: JobStatusEnum
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "job_12345",
                "status": "running",
                "progress": 45.5,
                "message": "Processing file 2 of 5",
                "estimated_completion": "2024-01-01T15:30:00Z"
            }
        }

class JobMetricsResponse(BaseModel):
    """Job metrics response schema"""
    job_id: str
    processing_time: int = Field(..., description="Processing time in seconds")
    memory_usage: int = Field(..., description="Memory usage in MB")
    cpu_usage: int = Field(..., description="CPU usage percentage")
    extracted_records: int = 0
    transformed_records: int = 0
    loaded_records: int = 0
    throughput: float = Field(..., description="Records per second")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "job_12345",
                "processing_time": 300,
                "memory_usage": 512,
                "cpu_usage": 75,
                "extracted_records": 10000,
                "transformed_records": 9500,
                "loaded_records": 9500,
                "throughput": 31.67
            }
        }

class JobListResponse(BaseModel):
    """Job list response schema"""
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "JobNotFound",
                "message": "Job with ID 'invalid_job' not found",
                "details": {}
            }
        }

class SuccessResponse(BaseModel):
    """Success response schema"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {}
            }
        }
