from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .base import CRUDBase
from ..models import Item, Chest
from ..schemas import ItemCreate


class CRUDItem(CRUDBase[Item, ItemCreate, ItemCreate]):
    """CRUD operations for Item model."""

    def get_by_chest(self, db: Session, chest_id: int) -> List[Item]:
        """
        Retrieve all items in the specified chest.
        
        Args:
            db: Database session
            chest_id: Chest primary key
            
        Returns:
            List of Item instances
        """
        stmt = select(Item).where(Item.chest_id == chest_id)
        return list(db.scalars(stmt).all())

    def get_summary_by_world(self, db: Session, world_id: int) -> dict[str, int]:
        """
        Retrieve a summary of items in all chests of the specified world.
        
        Optimized to use a single query with JOIN instead of N+1 queries.
        Groups items by name and sums their quantities.
        
        Args:
            db: Database session
            world_id: World primary key
            
        Returns:
            Dictionary mapping item names to total quantities
        """
        stmt = (
            select(Item.name, func.sum(Item.quantity))
            .join(Chest, Item.chest_id == Chest.id)
            .where(Chest.world_id == world_id)
            .group_by(Item.name)
        )
        
        results = db.execute(stmt).all()
        
        # Convert to dictionary
        return {name: int(total_quantity) for name, total_quantity in results}


# Create a singleton instance
item = CRUDItem(Item)
