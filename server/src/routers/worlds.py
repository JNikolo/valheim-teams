from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from valheim_save_tools_py import ValheimSaveTools, parse_items_from_base64
from ..database import get_db
from .. import crud, schemas

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

@router.post("/upload/", response_model=dict)
async def world_upload(
    db_file: Annotated[UploadFile, File(description="Valheim .db save file")], #UploadFile = File(..., description="Valheim .db save file"),
    fwl_file: Annotated[UploadFile, File(description="Valheim .fwl world file")],
    db: Session = Depends(get_db)
):
    """Upload Valheim world save files and store chests/items in database"""

    if db_file.content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail="Invalid .db file type")
    
    if fwl_file.content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail="Invalid .fwl file type")
    
    # Parse .db file (world save data)
    try:
        save_data = vst.to_json(db_file.file, input_file_type=".db")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing .db file: {str(e)}")
    
    if not save_data:
        raise HTTPException(status_code=500, detail="Failed to parse .db file or file is empty")
    
    # Parse .fwl file (world metadata)
    try:
        world_meta = vst.to_json(fwl_file.file, input_file_type=".fwl")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing .fwl file: {str(e)}")
    
    if not world_meta:
        raise HTTPException(status_code=500, detail="Failed to parse .fwl file or file is empty")
    
    save_data_meta: dict = save_data.get("meta", {})

    # Extract world data
    world_data = schemas.WorldCreate(
        version=save_data_meta.get("worldVersion", 0),
        net_time=save_data_meta.get("netTime", 0.0),
        modified_time=save_data_meta.get("modified", 0),
        name=world_meta.get("name", fwl_file.filename.replace(".fwl", "")),
        uid=world_meta.get("uid", 0),
        seed=world_meta.get("seed", 0),
        seed_name=world_meta.get("seedName", "")
    )

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
    
    return {
        "status": "success",
        "world_id": db_world.id,
        "world_uid": db_world.uid,
        "world_name": db_world.name,
        "total_chests": total_chests,
        "total_items": total_items,
        "message": f"Successfully saved {total_chests} chests and {total_items} items"
    }

