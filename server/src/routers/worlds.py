from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from valheim_save_tools_py import ValheimSaveTools
from ..database import get_db
from .. import schemas
from ..crud import crud, utils
from ..exceptions import WorldNotNewerError
from pydantic import BaseModel

vst = ValheimSaveTools(verbose=True)

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

def parse_valheim_files(vh_file: UploadFile, file_type: str):
    """Parse Valheim .db and .fwl files and return their JSON representations"""
    try:
        parsed_data = vst.to_json(vh_file.file, input_file_type=file_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing {file_type} file: {str(e)}")
    
    if not parsed_data:
        raise HTTPException(status_code=500, detail=f"Failed to parse {file_type} file or file is empty")

    return parsed_data

@router.get("/{world_id}/", response_model=schemas.World)
async def get_world(world_id: int, db: Session = Depends(get_db)):
    """Retrieve a world by its ID"""
    world = crud.get_world(db, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world

@router.get("/", response_model=list[schemas.World])
async def get_all_worlds(db: Session = Depends(get_db)):
    """Retrieve all worlds"""
    worlds = crud.get_all_worlds(db)
    if not worlds:
        raise HTTPException(status_code=404, detail="No worlds found")
    return worlds

@router.get("/{world_id}/chests/", response_model=list[schemas.Chest])
async def get_chests_in_world(world_id: int, db: Session = Depends(get_db)):
    chests = crud.get_chests_by_world(db, world_id)
    if not chests:
        raise HTTPException(status_code=404, detail="No chests found in the specified world")
    return chests

@router.get("/{world_id}/items/summary/", response_model=dict[str, int])
async def get_item_summary_in_world(world_id: int, db: Session = Depends(get_db)):
    """Retrieve a summary of items in the specified world"""
    item_summary = utils.get_item_summary_by_world(db, world_id)
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
    db_file, fwl_file = valheim_files

    save_data = parse_valheim_files(db_file, ".db")
    world_meta = parse_valheim_files(fwl_file, ".fwl")

    world_data = utils.extract_world_data(save_data, world_meta)

    try:
        with db.begin():
            existing_world = crud.get_world_by_uid(db, world_data.uid)
            
            world = utils.create_or_update_world(
                db,
                existing_world,
                world_data,
            )

            total_chests, total_items = utils.populate_inventory(
                db,
                world,
                save_data,
            )

    except WorldNotNewerError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
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