"""
Main entry point for the log application API.
"""
from fastapi import FastAPI
from mitra_ai_foundation.api.main import app as foundation_app
from api.routers.log_router import router as log_router

# Extend the foundation app with log application routes
foundation_app.include_router(log_router, prefix="/logs")

# Use the foundation app
app = foundation_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)