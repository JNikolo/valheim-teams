from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .base import CRUDBase
from ..models import World
from ..schemas import WorldCreate
from ..logging_config import get_logger

logger = get_logger(__name__)


class CRUDWorld(CRUDBase[World, WorldCreate, WorldCreate]):
    """CRUD operations for World model."""

    def get_by_uid(self, db: Session, uid: int) -> Optional[World]:
        """
        Retrieve a world by its unique identifier (uid).
        
        Args:
            db: Database session
            uid: World unique identifier
            
        Returns:
            World instance or None if not found
        """
        stmt = select(World).where(World.uid == uid)
        return db.scalars(stmt).first()

    def get_with_chests(self, db: Session, world_id: int) -> Optional[World]:
        """
        Retrieve a world by its ID with chests eagerly loaded.
        
        Avoids N+1 queries when accessing world.chests.
        
        Args:
            db: Database session
            world_id: World primary key
            
        Returns:
            World instance with chests loaded, or None if not found
        """
        stmt = (
            select(World)
            .where(World.id == world_id)
            .options(selectinload(World.chests))
        )
        return db.scalars(stmt).first()

    def update_by_id(
        self, db: Session, world_id: int, world_update: WorldCreate
    ) -> Optional[World]:
        """
        Update an existing world in the database.
        
        Args:
            db: Database session
            world_id: World primary key
            world_update: Updated world data
            
        Returns:
            Updated World instance or None if not found
        """
        db_world = self.get(db, world_id)
        if not db_world:
            return None

        update_data = world_update.model_dump()
        for field, value in update_data.items():
            setattr(db_world, field, value)

        db.flush()
        return db_world


# Create a singleton instance
world = CRUDWorld(World)
