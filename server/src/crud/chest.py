from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload

from .base import CRUDBase
from ..models import Chest
from ..schemas import ChestCreate
from ..logging_config import get_logger

logger = get_logger(__name__)


class CRUDChest(CRUDBase[Chest, ChestCreate, ChestCreate]):
    """CRUD operations for Chest model."""

    def get_by_world(self, db: Session, world_id: int) -> List[Chest]:
        """
        Retrieve all chests in the specified world.
        
        Args:
            db: Database session
            world_id: World primary key
            
        Returns:
            List of Chest instances
        """
        stmt = select(Chest).where(Chest.world_id == world_id)
        return list(db.scalars(stmt).all())

    def get_by_world_with_items(self, db: Session, world_id: int) -> List[Chest]:
        """
        Retrieve all chests in the specified world with items eagerly loaded.
        
        Avoids N+1 query problem by loading items in a single additional query.
        Use this when you need to access chest.items to prevent multiple database hits.
        
        Args:
            db: Database session
            world_id: World primary key
            
        Returns:
            List of Chest instances with items loaded
        """
        stmt = (
            select(Chest)
            .where(Chest.world_id == world_id)
            .options(selectinload(Chest.items))
        )
        return list(db.scalars(stmt).all())

    def count_by_world(self, db: Session, world_id: int) -> int:
        """
        Count total number of chests in a world.
        
        Args:
            db: Database session
            world_id: World primary key
            
        Returns:
            Total count of chests in the world
        """
        stmt = select(func.count()).select_from(Chest).where(Chest.world_id == world_id)
        return db.scalar(stmt) or 0

    def get_by_world_paginated(
        self, db: Session, world_id: int, skip: int = 0, limit: int = 100
    ) -> List[Chest]:
        """
        Retrieve chests in a world with pagination.
        
        Args:
            db: Database session
            world_id: World primary key
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Chest instances
        """
        stmt = (
            select(Chest)
            .where(Chest.world_id == world_id)
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def delete_by_world(self, db: Session, world_id: int) -> int:
        """
        Delete all chests in the specified world.
        
        Args:
            db: Database session
            world_id: World primary key
            
        Returns:
            Number of deleted chests
        """
        stmt = delete(Chest).where(Chest.world_id == world_id)
        result = db.execute(stmt)
        deleted_count = result.rowcount if result.rowcount is not None else 0
        logger.debug(f"Deleted {deleted_count} chests from world {world_id}")
        return deleted_count


# Create a singleton instance
chest = CRUDChest(Chest)
