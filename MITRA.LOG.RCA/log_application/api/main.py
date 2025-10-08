"""
Main entry point for the log application API.
"""
import os
from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())
from fastapi import FastAPI

from mitra_ai_foundation.common.config.config_manager import ConfigManager
from api.routers.log_router import router as log_router

from mitra_ai_foundation.common.config.config_manager import get_config_manager

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    config_manager = get_config_manager()
    config_manager.initialize() 
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")

from mitra_ai_foundation.api.main import app as foundation_app

# Extend the foundation app with log application routes
foundation_app.include_router(log_router, prefix="/logs")

# Use the foundation app
app = foundation_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)