from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from .. import models, schemas

#========================== CRUD Operations ==========================#
# These functions handle Create, Read, Update, and Delete operations
# for Chest and Item entities in the database.

#*************************** Chest Operations ***************************#
# READ OPERATIONS
def get_chest(db: Session, chest_id: int) -> models.Chest | None:
    """Retrieve a chest by its ID."""
    return db.get(models.Chest, chest_id)

def get_all_chests(db: Session) -> list[models.Chest]:
    """Retrieve all chests."""
    return db.scalars(select(models.Chest)).all()

def get_chests_by_world(db: Session, world_id: int) -> list[models.Chest]:
    """Retrieve all chests in the specified world."""
    return db.scalars(select(models.Chest).where(models.Chest.world_id == world_id)).all()

# CREATE OPERATIONS
def create_chest(db: Session, chest: schemas.ChestCreate) -> models.Chest:
    """Create a new chest in the database."""
    db_chest = models.Chest(
        world_id=chest.world_id,
        prefab_name=chest.prefab_name,
        creator_id=chest.creator_id,
        position_x=chest.position_x,
        position_y=chest.position_y,
        position_z=chest.position_z,
        sector_x=chest.sector_x,
        sector_y=chest.sector_y,
        rotation_x=chest.rotation_x,
        rotation_y=chest.rotation_y,
        rotation_z=chest.rotation_z,
    )
    db.add(db_chest)
    db.flush()
    return db_chest

def create_chests_bulk(db: Session, chests: list[schemas.ChestCreate]) -> list[models.Chest]:
    """Create multiple chests in the database using bulk insert."""
    db_chests = [
        models.Chest(
            world_id=chest.world_id,
            prefab_name=chest.prefab_name,
            creator_id=chest.creator_id,
            position_x=chest.position_x,
            position_y=chest.position_y,
            position_z=chest.position_z,
            sector_x=chest.sector_x,
            sector_y=chest.sector_y,
            rotation_x=chest.rotation_x,
            rotation_y=chest.rotation_y,
            rotation_z=chest.rotation_z,
        )
        for chest in chests
    ]
    db.add_all(db_chests)
    db.flush()
    return db_chests

# DELETE OPERATIONS
def delete_chests_by_world(db: Session, world_id: int) -> int:
    """Delete all chests in the specified world. Returns the number of deleted chests."""
    stmt = delete(models.Chest).where(models.Chest.world_id == world_id)
    result = db.execute(stmt)
    deleted_count = result.rowcount if result.rowcount is not None else 0
    return deleted_count

#*************************** Item Operations ***************************#
# READ OPERATIONS
def get_item(db: Session, item_id: int) -> models.Item | None:
    """Retrieve an item by its ID."""
    return db.get(models.Item, item_id)

def get_all_items_in_chest(db: Session, chest_id: int) -> list[models.Item]:
    """Retrieve all items in the specified chest."""
    return db.scalars(select(models.Item).where(models.Item.chest_id == chest_id)).all()

def get_all_items(db: Session) -> list[models.Item]:
    """Retrieve all items."""
    return db.scalars(select(models.Item)).all()

# CREATE OPERATIONS
def create_items_bulk(db: Session, items: list[schemas.ItemCreate]) -> None:
    """Create multiple items in the database using bulk insert."""
    db_items = [
        models.Item(
            chest_id=item.chest_id,
            name=item.name,
            quantity=item.quantity,
            quality=item.quality,
            durability=item.durability,
            position_x=item.position_x,
            position_y=item.position_y,
            equipped=item.equipped,
            variant=item.variant,
            crafter_id=item.crafter_id,
            crafter_name=item.crafter_name,
        )
        for item in items
    ]
    db.add_all(db_items)
    db.flush()

#************************** World Operations ***************************#
# READ OPERATIONS
def get_world(db: Session, world_id: int) -> models.World | None:
    """Retrieve a world by its ID."""
    return db.get(models.World, world_id)

def get_all_worlds(db: Session) -> list[models.World]:
    """Retrieve all worlds."""
    return db.scalars(select(models.World)).all()

def get_world_by_uid(db: Session, uid: int) -> models.World | None:
    """Retrieve a world by its unique identifier (uid)."""
    return db.scalars(select(models.World).where(models.World.uid == uid)).first()

# CREATE OPERATIONS
def create_world(db: Session, world: schemas.WorldCreate) -> models.World:
    """Create a new world in the database."""
    db_world = models.World(
        uid=world.uid,
        version=world.version,
        net_time=world.net_time,
        modified_time=world.modified_time,
        name=world.name,
        seed=world.seed,
        seed_name=world.seed_name,
    )
    db.add(db_world)
    db.flush()
    return db_world

# UPDATE OPERATIONS
def update_world(db: Session, world_id: int, world_update: schemas.WorldCreate) -> models.World | None:
    """Update an existing world in the database."""
    db_world = db.get(models.World, world_id)
    if not db_world:
        return None

    db_world.uid = world_update.uid
    db_world.version = world_update.version
    db_world.net_time = world_update.net_time
    db_world.modified_time = world_update.modified_time
    db_world.name = world_update.name
    db_world.seed = world_update.seed
    db_world.seed_name = world_update.seed_name

    db.flush()
    return db_world

#======================== End of CRUD Operations ========================#