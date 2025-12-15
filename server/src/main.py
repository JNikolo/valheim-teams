from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from src.database import engine, get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
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

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and readiness probes.
    
    Checks:
    - API is responsive
    - Database connection is working
    
    Returns:
        200: Service is healthy
        503: Service is unhealthy (database connection failed)
    """
    try:
        # Test database connection by checking if the session is valid
        # This is safer than using raw SQL and tests the ORM connection
        db.execute(select(1))
        logger.debug("Health check passed - database connection OK")
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed - database connection error: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )
