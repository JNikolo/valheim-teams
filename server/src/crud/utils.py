from . import crud
from .. import schemas, models
from sqlalchemy.orm import Session
from fastapi import HTTPException
from valheim_save_tools_py import parse_items_from_base64

CHEST_PREFABS = {
    "piece_chest",
    "piece_chest_wood",
    "piece_chest_iron",
    "piece_chest_blackmetal",
}

def populate_inventory(
    db: Session, 
    existing_world: models.World, 
    world_data: schemas.WorldCreate, 
    save_data: dict
) -> tuple[models.World, int, int]:
    """Populate the inventory for an existing world or create one."""
    
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
                world_id=db_world.id
            )

            # Save chest to database
            db_chest = crud.create_chest(db, chest_create)
            total_chests += 1

            # Parse items from chest
            chest_strings = chest_data.get('stringsByName', {})
            chest_items_string = chest_strings.get('items', '')
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
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")
    
    db.commit()
    return (db_world, total_chests, total_items)