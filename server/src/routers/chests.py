from fastapi import APIRouter, Depends
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

@router.get("/{chest_id}/items/", response_model=List[schemas.Item])
async def get_items_in_chest(chest_id: int, db: Session = Depends(get_db)):
    """Get all items in a chest by chest ID"""
    # First verify chest exists
    chest = crud.chest.get(db, chest_id)
    if not chest:
        raise ChestNotFoundError(chest_id)
    
    items = crud.item.get_by_chest(db, chest_id)
    
    if not items:
        logger.info(f"No items found in chest: {chest_id}")
        return []  # Return empty list instead of error
    
    return items