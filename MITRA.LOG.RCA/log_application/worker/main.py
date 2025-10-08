"""
Main entry point for the log application worker.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())

from mitra_ai_foundation.worker.core.celery_app import celery_app
from mitra_ai_foundation.common.config.config_manager import get_config_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variabl''es from .env file


# Initialize config manager with paths from environment variables
try:
    config_manager = get_config_manager()
    config_manager.initialize() 
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    # Continue execution even if config fails - we'll use defaults

# Import tasks to register them with Celery
from worker.tasks.log_tasks import process_logs, analyze_errors
if __name__ == "__main__":
    # Add arguments for Celery worker
    argv = [
        'worker',
        '--loglevel=INFO',
        '--concurrency=1',
        '--pool=solo',
    ]
    
    # Start the Celery worker process
    celery_app.worker_main(argv)