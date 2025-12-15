from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, crud
from ..exceptions import ItemNotFoundError
from ..logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/items",
    tags=["items"],
)

@router.get("/{item_id}", response_model=schemas.Item)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get a single item by item ID"""
    item = crud.item.get(db, item_id)
    
    if not item:
        logger.warning(f"Item not found: {item_id}")
        raise ItemNotFoundError(item_id)

    return item
