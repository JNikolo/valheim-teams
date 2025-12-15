from typing import Optional
from sqlalchemy.orm import Session

from .. import crud
from ..models import World
from ..schemas import WorldCreate
from ..exceptions import WorldNotNewerError
from ..logging_config import get_logger

logger = get_logger(__name__)


class WorldService:
    """
    Business logic service for World operations.
    
    Handles world-specific business rules and orchestrates CRUD operations.
    """

    @staticmethod
    def extract_world_data(save_data: dict, world_meta: dict) -> WorldCreate:
        """
        Extract world data from parsed save and metadata files.
        
        Args:
            save_data: Parsed .db save file data
            world_meta: Parsed .fwl world metadata
            
        Returns:
            WorldCreate schema with extracted data
        """
        save_data_meta: dict = save_data.get("meta", {})

        return WorldCreate(
            version=save_data_meta.get("worldVersion", 0),
            net_time=save_data_meta.get("netTime", 0.0),
            modified_time=save_data_meta.get("modified", 0),
            name=world_meta.get("name", ""),
            uid=world_meta.get("uid", 0),
            seed=world_meta.get("seed", 0),
            seed_name=world_meta.get("seedName", "")
        )

    @staticmethod
    def create_or_update_world(
        db: Session,
        world_data: WorldCreate
    ) -> tuple[World, bool]:
        """
        Create a new world or update an existing one based on UID.
        
        Business rule: Only allow updates if the new save is newer (higher net_time).
        
        Args:
            db: Database session
            world_data: World data to create or update
            
        Returns:
            Tuple of (world instance, was_created: bool)
            
        Raises:
            WorldNotNewerError: If trying to update with older/same save
        """
        existing = crud.world.get_by_uid(db, world_data.uid)

        if existing:
            logger.debug(
                f"World with UID {world_data.uid} exists (ID: {existing.id}). "
                f"Comparing net_time: new={world_data.net_time}, existing={existing.net_time}"
            )
            
            # Business rule: Prevent uploading older saves
            if world_data.net_time <= existing.net_time:
                logger.warning(
                    f"Rejected world update for UID {world_data.uid}: "
                    f"Upload net_time {world_data.net_time} is not newer than "
                    f"existing {existing.net_time}"
                )
                raise WorldNotNewerError(
                    f"Uploaded save is not newer than existing world. "
                    f"Upload net_time: {world_data.net_time}, "
                    f"Existing net_time: {existing.net_time}"
                )
            
            # Update existing world
            logger.info(
                f"Updating world {existing.name} (ID: {existing.id}) "
                f"with newer save (net_time: {world_data.net_time})"
            )
            world = crud.world.update_by_id(db, existing.id, world_data)
            return world, False

        # Create new world
        logger.info(f"Creating new world: {world_data.name} (UID: {world_data.uid})")
        world = crud.world.create(db, obj_in=world_data)
        logger.debug(f"World created with ID: {world.id}")
        return world, True


# Create a singleton instance
world_service = WorldService()
