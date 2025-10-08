"""
Base task definitions for the Celery worker.

This module provides the foundation for defining Celery tasks.
Specific applications should define their own tasks in their respective packages.
"""
from typing import Dict, Optional, Any
from ..core.celery_app import celery_app, update_task_progress
import time
import random
# No predefined tasks in the foundation
# Applications should define their own tasks by importing celery_app and update_task_progress
from ...common.enum.task_model import TaskType

@celery_app.task(bind=True, name=TaskType.LONG_RUNNING_TASK)
def long_running_task(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Example of a long-running task with progress updates.
    
    Args:
        self: Task instance (bound task)
        params: Optional parameters for the task
        
    Returns:
        Dictionary with task results
    """
    task_id = self.request.id
    iterations = params.get("iterations", 10) if params else 10
    
    for i in range(iterations):
        # Calculate progress percentage
        progress = int((i + 1) / iterations * 100)
        
        # Update progress in Redis
        update_task_progress(
            task_id, 
            progress, 
            f"Processing iteration {i+1}/{iterations}"
        )
        
        # Simulate work
        time.sleep(random.uniform(0.5, 1.5))
    
    return {
        "status": "completed",
        "iterations_processed": iterations,
        "processing_time": f"{iterations * 1.0:.2f} seconds (estimated)"
    }