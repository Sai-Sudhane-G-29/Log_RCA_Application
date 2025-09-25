"""
Database models for batch processing jobs
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class JobStatus(enum.Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchJob(Base):
    """Batch job model"""
    __tablename__ = "batch_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    job_type = Column(String(50), nullable=False)
    
    # Job configuration
    config = Column(JSON, nullable=True)
    log_files = Column(JSON, nullable=True)  # List of log files to process
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results and errors
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Processing metrics
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "status": self.status.value if self.status else None,
            "job_type": self.job_type,
            "config": self.config,
            "log_files": self.log_files,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": self.results,
            "error_message": self.error_message,
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "failed_records": self.failed_records,
        }

class JobQueue(Base):
    """Job queue model for managing job execution order"""
    __tablename__ = "job_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    queue_time = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "priority": self.priority,
            "queue_time": self.queue_time.isoformat() if self.queue_time else None,
        }

class SparkSession(Base):
    """Spark session tracking model"""
    __tablename__ = "spark_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    job_id = Column(String(50), index=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Session configuration
    spark_config = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "job_id": self.job_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "spark_config": self.spark_config,
        }

class JobMetadata(Base):
    """Job metadata and processing details"""
    __tablename__ = "job_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), index=True, nullable=False)
    
    # File processing details
    source_files = Column(JSON, nullable=True)
    processed_files = Column(JSON, nullable=True)
    failed_files = Column(JSON, nullable=True)
    
    # Processing statistics
    processing_time = Column(Integer, default=0)  # seconds
    memory_usage = Column(Integer, default=0)  # MB
    cpu_usage = Column(Integer, default=0)  # percentage
    
    # ETL statistics
    extracted_records = Column(Integer, default=0)
    transformed_records = Column(Integer, default=0)
    loaded_records = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "source_files": self.source_files,
            "processed_files": self.processed_files,
            "failed_files": self.failed_files,
            "processing_time": self.processing_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "extracted_records": self.extracted_records,
            "transformed_records": self.transformed_records,
            "loaded_records": self.loaded_records,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
