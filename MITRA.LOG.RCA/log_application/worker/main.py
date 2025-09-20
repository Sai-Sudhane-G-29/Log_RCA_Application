"""
Main entry point for the log application worker.
"""
from mitra_ai_foundation.worker.core.celery_app import celery_app

# Import tasks to register them with Celery
from worker.tasks import log_tasks

# Use the foundation celery app
app = celery_app

if __name__ == "__main__":
    app.start()