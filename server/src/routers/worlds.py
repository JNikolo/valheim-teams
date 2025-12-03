from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from valheim_save_tools_py import ValheimSaveTools, parse_items_from_base64
from ..database import get_db
from .. import schemas
from ..crud import crud

vst = ValheimSaveTools(verbose=True)

CHEST_PREFABS = {
    "piece_chest",
    "piece_chest_wood",
    "piece_chest_iron",
    "piece_chest_blackmetal",
}

router = APIRouter(
    prefix="/worlds",
    tags=["worlds"],
)

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

def extract_world_data(save_data: dict, world_meta: dict) -> schemas.WorldCreate:
    """Extract world data from parsed save and meta data"""
    save_data_meta: dict = save_data.get("meta", {})

    world_data = schemas.WorldCreate(
        version=save_data_meta.get("worldVersion", 0),
        net_time=save_data_meta.get("netTime", 0.0),
        modified_time=save_data_meta.get("modified", 0),
        name=world_meta.get("name", ""),
        uid=world_meta.get("uid", 0),
        seed=world_meta.get("seed", 0),
        seed_name=world_meta.get("seedName", "")
    )
    return world_data

def process_chest_items(db: Session, found_chests: list[dict], world_id: int):
    total_chests = 0
    total_items = 0

    for chest_data in found_chests:
        # Extract chest data
        position: dict = chest_data.get("position", {})
        sector: dict = chest_data.get("sector", {})
        rotation: dict = chest_data.get("rotation", {})
        longs: dict = chest_data.get("longsByName", {})

        # Create chest schema for validation
        chest_create = schemas.ChestCreate(
            prefab_name=chest_data.get("prefabName", ""),
            creator_id=longs.get("creator", 0),
            position_x=position.get("x", 0.0),
            position_y=position.get("y", 0.0),
            position_z=position.get("z", 0.0),
            sector_x=sector.get("x", 0),
            sector_y=sector.get("y", 0),
            rotation_x=rotation.get("x", 0.0),
            rotation_y=rotation.get("y", 0.0),
            rotation_z=rotation.get("z", 0.0),
            world_id=world_id
        )

        # Save chest to database
        db_chest = crud.create_chest(db, chest_create)
        total_chests += 1

        # Parse items from chest
        chest_strings: dict = chest_data.get('stringsByName', {})
        chest_items_string: str = chest_strings.get('items', '')
        chest_items: list[dict] = parse_items_from_base64(chest_items_string)
        
        # Save each item to database
        for item_data in chest_items:
            item_create = schemas.ItemCreate(
                chest_id=db_chest.id,
                name=item_data.get("name", ""),
                quantity=item_data.get("stack", 0),
                durability=item_data.get("durability", 100.0),
                position_x=item_data.get("pos_x", 0),
                position_y=item_data.get("pos_y", 0),
                equipped=item_data.get("equipped", False),
                variant=item_data.get("variant", 0),
                crafter_id=item_data.get("crafter_id", 0),
                crafter_name=item_data.get("crafter_name"),
                quality=item_data.get("quality", 0)
            )
            crud.create_item(db, item_create)
            total_items += 1
    
    return total_chests, total_items


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

@router.get("/{world_id}/items/summary/", response_model=dict)
async def get_item_summary_in_world(world_id: int, db: Session = Depends(get_db)):
    """Retrieve a summary of items in the specified world"""
    item_summary = crud.get_item_summary_by_world(db, world_id)
    if not item_summary:
        raise HTTPException(status_code=404, detail="No items found in the specified world")
    return item_summary

@router.post("/upload/", response_model=schemas.World)
async def world_upload(
    valheim_files: Annotated[tuple[UploadFile, UploadFile], Depends(validate_valheim_files)],
    db: Session = Depends(get_db)
):
    """Upload Valheim world save files and store chests/items in database"""

    db_file, fwl_file = valheim_files # Unpack validated files
    
    # Parse files to JSON using ValheimSaveTools
    save_data = parse_valheim_files(db_file, ".db")
    world_meta = parse_valheim_files(fwl_file, ".fwl")
    
    # Extract world data
    world_data = extract_world_data(save_data, world_meta)

    # Check if world exists by UID
    existing_world = crud.get_world_by_uid(db, world_data.uid)
    
    if existing_world:
        if world_data.modified_time <= existing_world.modified_time:
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded save is not newer. Current: {existing_world.modified_time}, Uploaded: {world_data.modified_time}"
            )
        
        # Update existing world
        crud.delete_chests_by_world(db, existing_world.id)
        db_world = crud.update_world(db, existing_world.id, world_data)
    else:
        # Create new world
        db_world = crud.create_world(db, world_data)

    zdoList = save_data.get("zdoList", [])
    found_chests = [zdo for zdo in zdoList if zdo.get("prefabName", "") in CHEST_PREFABS]
    total_chests = 0
    total_items = 0

    try:
        for chest_data in found_chests:
            # Extract chest data
            position = chest_data.get("position", {})
            sector = chest_data.get("sector", {})
            rotation = chest_data.get("rotation", {})
            longs = chest_data.get("longsByName", {})

            # Create chest schema for validation
            chest_create = schemas.ChestCreate(
                prefab_name=chest_data.get("prefabName", ""),
                creator_id=longs.get("creator", 0),
                position_x=position.get("x", 0.0),
                position_y=position.get("y", 0.0),
                position_z=position.get("z", 0.0),
                sector_x=sector.get("x", 0),
                sector_y=sector.get("y", 0),
                rotation_x=rotation.get("x", 0.0),
                rotation_y=rotation.get("y", 0.0),
                rotation_z=rotation.get("z", 0.0),
                world_id=db_world.id
            )

            # Save chest to database
            db_chest = crud.create_chest(db, chest_create)
            total_chests += 1

            # Parse items from chest
            chest_strings = chest_data.get('stringsByName', {})
            chest_items_string = chest_strings.get('items', '')
            chest_items = parse_items_from_base64(chest_items_string)
            
            # Save each item to database
            for item_data in chest_items:
                item_create = schemas.ItemCreate(
                    chest_id=db_chest.id,
                    name=item_data.get("name", ""),
                    quantity=item_data.get("stack", 0),
                    durability=item_data.get("durability", 100.0),
                    position_x=item_data.get("pos_x", 0),
                    position_y=item_data.get("pos_y", 0),
                    equipped=item_data.get("equipped", False),
                    variant=item_data.get("variant", 0),
                    crafter_id=item_data.get("crafter_id", 0),
                    crafter_name=item_data.get("crafter_name"),
                    quality=item_data.get("quality", 0)
                )
                crud.create_item(db, item_create)
                total_items += 1
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")
    
    return db_world

