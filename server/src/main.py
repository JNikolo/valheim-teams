from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from src.database import engine, get_db
from sqlalchemy.orm import Session
from . import schemas, crud
from .models import Base
from .routers import worlds
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

@app.get("/")
def read_root():
    """API root endpoint - health check"""
    logger.debug("Root endpoint accessed")
    return {
        "message": "Valheim Teams API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/items/{item_id}", response_model=schemas.Item)
async def get_items(item_id: int, db: Session = Depends(get_db)):
    """Get a single item by ID (test endpoint)"""
    logger.debug(f"Fetching item with ID: {item_id}")
    item = crud.item.get(db, item_id)
    
    if not item:
        logger.warning(f"Item not found: {item_id}")
        raise HTTPException(status_code=404, detail="Item not found")
    
    logger.debug(f"Item found: {item.name} (quantity: {item.quantity})")
    return item

@app.get("/chests/{chest_id}/items/", response_model=list[schemas.Item])
async def get_items_in_chest(chest_id: int, db: Session = Depends(get_db)):
    """Get all items in a chest (test endpoint)"""
    logger.debug(f"Fetching items for chest ID: {chest_id}")
    items = crud.item.get_by_chest(db, chest_id)
    
    if not items:
        logger.warning(f"No items found in chest: {chest_id}")
        raise HTTPException(status_code=404, detail="No items found in the specified chest")
    
    logger.debug(f"Found {len(items)} items in chest {chest_id}")
    return items
