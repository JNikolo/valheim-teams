from fastapi import APIRouter, Depends, Query
from typing import List
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..exceptions import ChestNotFoundError
from ..logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chests",
    tags=["chests"],
)

@router.get("/{chest_id}/items/", response_model=schemas.PaginatedResponse[schemas.Item])
async def get_items_in_chest(
    chest_id: int,
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all items in a chest by chest ID with pagination.
    
    Returns paginated list of items with metadata.
    """
    # First verify chest exists
    chest = crud.chest.get(db, chest_id)
    if not chest:
        raise ChestNotFoundError(chest_id)
    
    # Get total count of items in this chest
    total = crud.item.count_by_chest(db, chest_id)
    
    # Get paginated results
    items = crud.item.get_by_chest_paginated(db, chest_id, skip=skip, limit=limit)
    
    logger.debug(f"Found {len(items)} item(s) out of {total} total in chest {chest_id}")
    
    return schemas.PaginatedResponse.create(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )