"""
Configuration settings for the batch processing engine
"""

from pydantic import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Batch Processing Engine"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/batch_processing"
    
    # DorisDB settings
    DORIS_HOST: str = "localhost"
    DORIS_PORT: int = 8030
    DORIS_USERNAME: str = "root"
    DORIS_PASSWORD: str = ""
    DORIS_DATABASE: str = "log_etl"
    
    # Spark settings
    SPARK_MASTER: str = "local[*]"
    SPARK_APP_NAME: str = "LogETLBatchProcessor"
    SPARK_DRIVER_MEMORY: str = "2g"
    SPARK_EXECUTOR_MEMORY: str = "2g"
    
    # Job queue settings
    REDIS_URL: str = "redis://localhost:6379/0"
    JOB_QUEUE_NAME: str = "batch_jobs"
    MAX_CONCURRENT_JOBS: int = 5
    JOB_TIMEOUT: int = 3600  # 1 hour
    
    # Log file settings
    LOG_FILES_PATH: str = "/var/log/batch_processing"
    PROCESSED_FILES_PATH: str = "/var/log/processed"
    
    # Processing settings
    BATCH_SIZE: int = 1000
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 60  # seconds
    
    # Monitoring settings
    STATUS_CHECK_INTERVAL: int = 30  # seconds
    CLEANUP_INTERVAL: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
