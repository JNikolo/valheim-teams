from fastapi import APIRouter, File, UploadFile, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud, services
from ..exceptions import (
    WorldNotNewerError,
    WorldNotFoundError,
    InvalidFileFormatError
)
from ..logging_config import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter(
    prefix="/worlds",
    tags=["worlds"],
)

class WorldUploadResponse(BaseModel):
    world_id: int
    world_name: str
    total_chests: int
    total_items: int

# Dependency to validate uploaded Valheim files
async def validate_valheim_files(
    db_file: Annotated[UploadFile, File(description="Valheim .db save file")],
    fwl_file: Annotated[UploadFile, File(description="Valheim .fwl world file")]
):
    """Dependency to validate uploaded Valheim files"""
    logger.debug(f"Validating uploaded files: {db_file.filename}, {fwl_file.filename}")
    
    if db_file.content_type != "application/octet-stream":
        logger.warning(f"Invalid .db file type: {db_file.content_type}")
        raise InvalidFileFormatError(".db", "Invalid content type")
    
    if fwl_file.content_type != "application/octet-stream":
        logger.warning(f"Invalid .fwl file type: {fwl_file.content_type}")
        raise InvalidFileFormatError(".fwl", "Invalid content type")
    
    if not db_file.filename.endswith(".db"):
        logger.warning(f"File does not have .db extension: {db_file.filename}")
        raise InvalidFileFormatError(".db", "File must have .db extension")
    if not fwl_file.filename.endswith(".fwl"):
        logger.warning(f"File does not have .fwl extension: {fwl_file.filename}")
        raise InvalidFileFormatError(".fwl", "File must have .fwl extension")
    
    logger.debug("File validation passed")
    return db_file, fwl_file

@router.get("/{world_id}/", response_model=schemas.World)
async def get_world(world_id: int, db: Session = Depends(get_db)):
    """Retrieve a world by its ID"""
    logger.debug(f"Fetching world with ID: {world_id}")
    world = crud.world.get(db, world_id)
    
    if not world:
        logger.warning(f"World not found: {world_id}")
        raise WorldNotFoundError(world_id)
    
    logger.debug(f"World found: {world.name} (UID: {world.uid})")
    return world

@router.get("/", response_model=list[schemas.World])
async def get_all_worlds(db: Session = Depends(get_db)):
    """Retrieve all worlds"""
    logger.debug("Fetching all worlds")
    worlds = crud.world.get_all(db)
    
    if not worlds:
        logger.info("No worlds found in database")
        return []  # Return empty list instead of error
    
    logger.debug(f"Found {len(worlds)} world(s)")
    return worlds

@router.get("/{world_id}/chests/", response_model=list[schemas.Chest])
async def get_chests_in_world(world_id: int, db: Session = Depends(get_db)):
    """Retrieve all chests in the specified world"""
    logger.debug(f"Fetching chests for world ID: {world_id}")
    
    # First verify world exists
    world = crud.world.get(db, world_id)
    if not world:
        raise WorldNotFoundError(world_id)
    
    chests = crud.chest.get_by_world(db, world_id)
    
    if not chests:
        logger.info(f"No chests found in world: {world_id}")
        return []  # Return empty list instead of error
    
    logger.debug(f"Found {len(chests)} chest(s) in world {world_id}")
    return chests

@router.get("/{world_id}/items/summary/", response_model=dict[str, int])
async def get_item_summary_in_world(world_id: int, db: Session = Depends(get_db)):
    """Retrieve a summary of items in the specified world"""
    logger.debug(f"Fetching item summary for world ID: {world_id}")
    
    # First verify world exists
    world = crud.world.get(db, world_id)
    if not world:
        raise WorldNotFoundError(world_id)
    
    item_summary = crud.item.get_summary_by_world(db, world_id)
    
    if not item_summary:
        logger.info(f"No items found in world: {world_id}")
        return {}  # Return empty dict instead of error
    
    total_items = sum(item_summary.values())
    logger.debug(f"Found {len(item_summary)} unique item types, {total_items} total items in world {world_id}")
    return item_summary

@router.post("/upload/", response_model=WorldUploadResponse)
def world_upload(
    valheim_files: Annotated[
        tuple[UploadFile, UploadFile],
        Depends(validate_valheim_files),
    ],
    db: Session = Depends(get_db),
):
    """
    Upload Valheim world save files (.db and .fwl) and populate the database.
    
    Extracts world metadata, chests, and items from the save files and
    stores them in the database. Updates existing worlds if the save is newer.
    """
    db_file, fwl_file = valheim_files
    
    logger.info(f"Processing world upload: {db_file.filename}, {fwl_file.filename}")

    # Parse the save files
    logger.debug("Parsing .db save file...")
    save_data = services.valheim_parser.parse_db_file(db_file.file)
    
    logger.debug("Parsing .fwl world metadata file...")
    world_meta = services.valheim_parser.parse_fwl_file(fwl_file.file)

    # Extract world data
    logger.debug("Extracting world data from parsed files...")
    world_data = services.world_service.extract_world_data(save_data, world_meta)
    logger.info(f"Extracted world data: {world_data.name} (UID: {world_data.uid})")

    try:
        with db.begin():
            # Create or update world
            logger.debug("Creating or updating world...")
            world, was_created = services.world_service.create_or_update_world(
                db,
                world_data,
            )
            
            action = "Created" if was_created else "Updated"
            logger.info(f"{action} world: {world.name} (ID: {world.id})")

            # Populate inventory (chests and items)
            logger.debug("Populating world inventory...")
            total_chests, total_items = services.inventory_service.populate_inventory(
                db,
                world,
                save_data,
            )
            
            logger.info(
                f"World upload successful - {world.name}: "
                f"{total_chests} chests, {total_items} items"
            )

    except WorldNotNewerError:
        # Let the exception bubble up to the global handler
        raise

    except Exception as e:
        logger.exception(f"Failed to process world upload: {str(e)}")
        # Re-raise to let global handler deal with it
        raise

    return WorldUploadResponse(
        world_id=world.id,
        world_name=world.name,
        total_chests=total_chests,
        total_items=total_items,
    )