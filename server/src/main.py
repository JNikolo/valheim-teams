from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from src.database import engine, get_db
from sqlalchemy.orm import Session
from . import schemas, crud
from .models import Base
from .routers import worlds, chests, items
from .logging_config import setup_logging, get_logger
from .middleware import RequestLoggingMiddleware, RequestIdContextMiddleware

# Initialize logging before anything else
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code: Initialize the database
    logger.info("Starting up Valheim Teams API...")
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown code
    logger.info("Shutting down Valheim Teams API...")

app = FastAPI(
    title="Valheim Teams API",
    version="1.0.0",
    description="API for managing Valheim world inventories and team resources",
    lifespan=lifespan
)

# Add middleware (order matters - last added is executed first)
app.add_middleware(RequestIdContextMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(worlds.router)
app.include_router(chests.router)
app.include_router(items.router)

@app.get("/")
def read_root():
    """API root endpoint - health check"""
    logger.debug("Root endpoint accessed")
    return {
        "message": "Valheim Teams API",
        "version": "1.0.0",
        "status": "running"
    }
