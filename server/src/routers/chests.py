from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chests",
    tags=["chests"],
)

@router.get("/{chest_id}/items/", response_model=List[schemas.Item])
async def get_items_in_chest(chest_id: int, db: Session = Depends(get_db)):
    """Get all items in a chest by chest ID"""
    items = crud.item.get_by_chest(db, chest_id)
    
    if not items:
        logger.warning(f"No items found in chest: {chest_id}")
        raise HTTPException(status_code=404, detail="No items found in the specified chest")
    
    return items