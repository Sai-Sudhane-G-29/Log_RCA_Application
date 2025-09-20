"""
Main entry point for the Celery worker.
"""
import os
import sys
import importlib
from worker.core.celery_app import celery_app

# Import task modules to register them with Celery
# This approach avoids Windows permission issues with the include parameter
import worker.tasks  # Main tasks module
importlib.import_module('worker.tasks.demo_tasks')  # Demo tasks module

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