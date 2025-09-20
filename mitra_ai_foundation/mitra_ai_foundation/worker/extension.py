"""
Extension mechanism for the worker package.
This module provides utilities for extending the worker with custom tasks.
"""
from typing import Callable, Dict, Any, List, Optional
from worker.core.celery_app import celery_app


def register_task(task_function: Callable) -> Callable:
    """
    Register a function as a Celery task.
    This is a convenience wrapper around celery_app.task decorator.
    
    Args:
        task_function: The function to register as a task
        
    Returns:
        The decorated function as a Celery task
    """
    return celery_app.task(bind=True)(task_function)


class WorkerExtension:
    """
    Helper class for extending the worker with custom tasks.
    """
    
    def __init__(self, namespace: str):
        """
        Initialize a worker extension.
        
        Args:
            namespace: The namespace for the extension tasks
        """
        self.namespace = namespace
        self.tasks: Dict[str, Callable] = {}
        
    def register_task(self, name: Optional[str] = None) -> Callable:
        """
        Decorator to register a function as a task in this extension.
        
        Args:
            name: Optional custom name for the task
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            task_name = name or func.__name__
            qualified_name = f"{self.namespace}.{task_name}"
            
            # Register with Celery
            task_func = celery_app.task(bind=True, name=qualified_name)(func)
            
            # Store in our registry
            self.tasks[task_name] = task_func
            return task_func
            
        return decorator
    
    def get_tasks(self) -> Dict[str, Callable]:
        """
        Get all registered tasks in this extension.
        
        Returns:
            Dictionary of task name to task function
        """
        return self.tasks