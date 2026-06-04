"""
Fashion Discovery Sub-Agent
Main application entry point
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from src.api import endpoints
from src.utils import logger

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
log = logger.setup_logger(__name__)

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    log.info("Starting Fashion Discovery Sub-Agent...")
    
    # Initialize database
    from src.database import db
    from src.database.seed import seed_database
    db.initialize()
    
    # Seed database if needed
    stats = {}
    try:
        from src.services.registry import registry_service
        stats = await registry_service.get_stats()
        if stats["total_retailers"] == 0:
            log.info("Registry empty, seeding with sample data...")
            seed_database()
    except Exception as e:
        log.warning(f"Could not check registry: {str(e)}")
    
    yield
    # Shutdown
    log.info("Shutting down Fashion Discovery Sub-Agent...")
    try:
        db.close()
    except Exception as e:
        log.warning(f"Error closing database: {str(e)}")

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(endpoints.router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fashion Discovery Sub-Agent",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
