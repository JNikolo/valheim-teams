from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.database import engine, get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from .models import Base
from .routers import worlds, chests, items
from .logging_config import setup_logging, get_logger
from .middleware import RequestLoggingMiddleware, RequestIdContextMiddleware
from .exceptions import ValheimAPIException, ResourceNotFoundError
from .config import settings

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

# Add exception handlers
@app.exception_handler(ValheimAPIException)
async def valheim_exception_handler(request: Request, exc: ValheimAPIException):
    """Handle all custom Valheim API exceptions."""
    logger.warning(f"API exception: {exc.message}", extra={"status_code": exc.status_code})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_type": exc.__class__.__name__
        }
    )


@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    """Handle resource not found exceptions."""
    logger.info(f"Resource not found: {exc.message}")
    return JSONResponse(
        status_code=404,
        content={
            "detail": exc.message,
            "resource_type": exc.resource_type,
            "resource_id": str(exc.resource_id)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors from Pydantic."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors."""
    logger.error(f"Database error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "A database error occurred",
            "error_type": "DatabaseError"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions."""
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "error_type": "InternalServerError"
        }
    )


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

logger.info(f"CORS enabled for origins: {settings.cors_origins}")

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
