from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud, services
from ..exceptions import WorldNotNewerError
from pydantic import BaseModel

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
    if db_file.content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail="Invalid .db file type")
    
    if fwl_file.content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail="Invalid .fwl file type")
    
    if not db_file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a .db file")
    if not fwl_file.filename.endswith(".fwl"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a .fwl file")
    
    return db_file, fwl_file

@router.get("/{world_id}/", response_model=schemas.World)
async def get_world(world_id: int, db: Session = Depends(get_db)):
    """Retrieve a world by its ID"""
    world = crud.world.get(db, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world

@router.get("/", response_model=list[schemas.World])
async def get_all_worlds(db: Session = Depends(get_db)):
    """Retrieve all worlds"""
    worlds = crud.world.get_all(db)
    if not worlds:
        raise HTTPException(status_code=404, detail="No worlds found")
    return worlds

@router.get("/{world_id}/chests/", response_model=list[schemas.Chest])
async def get_chests_in_world(world_id: int, db: Session = Depends(get_db)):
    """Retrieve all chests in the specified world"""
    chests = crud.chest.get_by_world(db, world_id)
    if not chests:
        raise HTTPException(status_code=404, detail="No chests found in the specified world")
    return chests

@router.get("/{world_id}/items/summary/", response_model=dict[str, int])
async def get_item_summary_in_world(world_id: int, db: Session = Depends(get_db)):
    """Retrieve a summary of items in the specified world"""
    item_summary = crud.item.get_summary_by_world(db, world_id)
    if not item_summary:
        raise HTTPException(status_code=404, detail="No items found in the specified world")
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

    # Parse the save files
    save_data = services.valheim_parser.parse_db_file(db_file.file)
    world_meta = services.valheim_parser.parse_fwl_file(fwl_file.file)

    # Extract world data
    world_data = services.world_service.extract_world_data(save_data, world_meta)

    try:
        with db.begin():
            # Create or update world
            world, was_created = services.world_service.create_or_update_world(
                db,
                world_data,
            )

            # Populate inventory (chests and items)
            total_chests, total_items = services.inventory_service.populate_inventory(
                db,
                world,
                save_data,
            )

    except WorldNotNewerError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Log the actual error for debugging
        import logging
        logging.exception("Failed to process world upload")
        raise HTTPException(
            status_code=500,
            detail="Failed to process world upload",
        )

    return WorldUploadResponse(
        world_id=world.id,
        world_name=world.name,
        total_chests=total_chests,
        total_items=total_items,
    )