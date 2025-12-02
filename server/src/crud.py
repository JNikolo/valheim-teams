from sqlalchemy.orm import Session
from sqlalchemy import select
from . import models, schemas

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

# CREATE OPERATIONS
def create_chest(db: Session, chest: schemas.ChestCreate) -> models.Chest:
    """Create a new chest in the database."""
    db_chest = models.Chest(
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
    db.commit()
    db.refresh(db_chest)
    return db_chest

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
def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    """Create a new item in the database."""
    db_item = models.Item(
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
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
