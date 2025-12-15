from . import crud
from .. import schemas, models
from sqlalchemy.orm import Session
from valheim_save_tools_py import parse_items_from_base64
from ..exceptions import WorldNotNewerError

CHEST_PREFABS = {
    "piece_chest",
    "piece_chest_wood",
    "piece_chest_iron",
    "piece_chest_blackmetal",
}

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

def extract_chest_data(chest_data: dict, world_id: int) -> schemas.ChestCreate:
    """Extract chest data from zdo entry"""
    position: dict = chest_data.get("position", {})
    sector: dict = chest_data.get("sector", {})
    rotation: dict = chest_data.get("rotation", {})
    longs: dict = chest_data.get("longsByName", {})

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
    return chest_create

def extract_item_data(item_data: dict, chest_id: int) -> schemas.ItemCreate:
    """Extract item data from parsed item dictionary"""
    item_create = schemas.ItemCreate(
        chest_id=chest_id,
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
    return item_create

def populate_inventory(
    db: Session,
    world: models.World,
    save_data: dict,
) -> tuple[int, int]:
    """
    Populate chests and items for an already-created world.
    Assumes:
      - world exists
      - validation already happened
      - transaction is managed by caller
    """

    zdo_list = save_data.get("zdoList", [])
    chest_zdos = [
        zdo for zdo in zdo_list
        if zdo.get("prefabName") in CHEST_PREFABS
    ]

    print(f"Populating inventory for world {world.id}: found {len(chest_zdos)} chests")

    # Remove old data
    crud.delete_chests_by_world(db, world.id)

    # -------- Create chests --------
    chest_creates: list[schemas.ChestCreate] = [
        extract_chest_data(zdo, world.id)
        for zdo in chest_zdos
    ]

    db_chests = crud.create_chests_bulk(db, chest_creates)

    # -------- Create items --------
    item_creates: list[schemas.ItemCreate] = []

    for db_chest, zdo in zip(db_chests, chest_zdos):
        chest_strings = zdo.get("stringsByName", {})
        items_blob = chest_strings.get("items", "")

        try:
            items = parse_items_from_base64(items_blob)
        except Exception:
            print(f"Failed to parse items for chest {db_chest.id} in world {world.id}")
            continue

        for item in items:
            item_creates.append(
                extract_item_data(item, db_chest.id)
            )

    if item_creates:
        crud.create_items_bulk(db, item_creates)

    print(f"Created {len(db_chests)} chests and {len(item_creates)} items for world {world.id}")

    return len(db_chests), len(item_creates)

def create_or_update_world(
    db: Session,
    existing: models.World | None,
    world_data: schemas.WorldCreate,
) -> models.World:
    if existing:
        if world_data.net_time <= existing.net_time:
            print(f"Uploaded world net_time {world_data.net_time} is not newer than existing {existing.net_time}")
            raise WorldNotNewerError(
                "Uploaded save is not newer than existing world"
            )
        return crud.update_world(db, existing.id, world_data)

    return crud.create_world(db, world_data)

def get_item_summary_by_world(db: Session, world_id: int) -> dict[str, int]:
    """Retrieve a summary of items in all chests of the specified world."""
    item_summary = {}
    chests = crud.get_chests_by_world(db, world_id)
    for chest in chests:
        items = crud.get_all_items_in_chest(db, chest.id)
        for item in items:
            if item.name in item_summary:
                item_summary[item.name] += item.quantity
            else:
                item_summary[item.name] = item.quantity
    return item_summary