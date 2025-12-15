import logging
from sqlalchemy.orm import Session
from valheim_save_tools_py import parse_items_from_base64

from .. import crud
from ..models import World
from ..schemas import ChestCreate, ItemCreate
from ..logging_config import get_logger

# Set up logger
logger = get_logger(__name__)

# Valheim chest prefab names
CHEST_PREFABS = frozenset([
    "piece_chest",
    "piece_chest_wood",
    "piece_chest_iron",
    "piece_chest_blackmetal",
])


class InventoryService:
    """
    Business logic service for inventory operations.
    
    Handles extraction and population of chests and items from Valheim save data.
    """

    @staticmethod
    def extract_chest_data(chest_data: dict, world_id: int) -> ChestCreate:
        """
        Extract chest data from a ZDO (Zone Data Object) entry.
        
        Args:
            chest_data: Raw chest data from save file
            world_id: ID of the world this chest belongs to
            
        Returns:
            ChestCreate schema with extracted data
        """
        position: dict = chest_data.get("position", {})
        sector: dict = chest_data.get("sector", {})
        rotation: dict = chest_data.get("rotation", {})
        longs: dict = chest_data.get("longsByName", {})

        return ChestCreate(
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

    @staticmethod
    def extract_item_data(item_data: dict, chest_id: int) -> ItemCreate:
        """
        Extract item data from parsed item dictionary.
        
        Args:
            item_data: Raw item data from save file
            chest_id: ID of the chest this item belongs to
            
        Returns:
            ItemCreate schema with extracted data
        """
        return ItemCreate(
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

    @staticmethod
    def populate_inventory(
        db: Session,
        world: World,
        save_data: dict,
    ) -> tuple[int, int]:
        """
        Populate chests and items for a world from save data.
        
        Business logic:
        1. Extract all chest ZDOs from save data
        2. Delete existing chests for this world (cascade deletes items)
        3. Create new chests in bulk
        4. Parse items from each chest and create in bulk
        
        Args:
            db: Database session
            world: World instance to populate inventory for
            save_data: Parsed .db save file data
            
        Returns:
            Tuple of (total_chests_created, total_items_created)
            
        Note:
            Assumes transaction is managed by caller.
            Assumes world already exists and validation has occurred.
        """
        zdo_list = save_data.get("zdoList", [])
        
        # Filter for chest ZDOs only
        chest_zdos = [
            zdo for zdo in zdo_list
            if zdo.get("prefabName") in CHEST_PREFABS
        ]

        logger.info(
            f"Populating inventory for world {world.id} ({world.name}): "
            f"found {len(chest_zdos)} chests"
        )

        # Delete old inventory data (cascade will delete items)
        deleted_count = crud.chest.delete_by_world(db, world.id)
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} old chests from world {world.id}")

        # Extract and create chests
        chest_creates = [
            InventoryService.extract_chest_data(zdo, world.id)
            for zdo in chest_zdos
        ]

        db_chests = crud.chest.create_bulk(db, objs_in=chest_creates)

        # Extract and create items
        item_creates: list[ItemCreate] = []

        for db_chest, zdo in zip(db_chests, chest_zdos):
            chest_strings = zdo.get("stringsByName", {})
            items_blob = chest_strings.get("items", "")

            try:
                items = parse_items_from_base64(items_blob)
            except Exception as e:
                logger.warning(
                    f"Failed to parse items for chest {db_chest.id} "
                    f"in world {world.id}: {e}"
                )
                continue

            for item in items:
                item_creates.append(
                    InventoryService.extract_item_data(item, db_chest.id)
                )

        if item_creates:
            crud.item.create_bulk(db, objs_in=item_creates)

        logger.info(
            f"Created {len(db_chests)} chests and {len(item_creates)} items "
            f"for world {world.id}"
        )

        return len(db_chests), len(item_creates)


# Create a singleton instance
inventory_service = InventoryService()
