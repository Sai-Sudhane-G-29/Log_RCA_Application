"""
FastAPI Batch Processing Engine
Main application entry point for log ETL batch processing system
"""

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api.src.routers.routes import router as main_router
from api.src.core.config import settings
from api.src.core.logging import setup_logging
from api.src.services.background_processor import BackgroundProcessor
from api.src.db.database import database

# Global background processor instance
background_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global background_processor
    
    # Startup
    await database.connect()
    background_processor = BackgroundProcessor()
    await background_processor.start()
    
    yield
    
    # Shutdown
    if background_processor:
        await background_processor.stop()
    await database.disconnect()

app = FastAPI(
    title="Batch Processing Engine",
    description="Log ETL Batch Processing System with FastAPI, Spark, and DorisDB",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main router
app.include_router(main_router, prefix="/batch")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Batch Processing Engine is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if database.is_connected else "disconnected",
        "background_processor": "running" if background_processor and background_processor.is_running else "stopped"
    }

if __name__ == "__main__":
    setup_logging()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
