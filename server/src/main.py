from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from src.database import engine, get_db
from sqlalchemy.orm import Session
from . import schemas, crud, models
from .routers import worlds


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code: Initialize the database
    models.Base.metadata.create_all(bind=engine)
    yield
    # Shutdown code: (if any needed)

app = FastAPI(lifespan=lifespan)

app.include_router(worlds.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}", response_model=schemas.Item)
async def get_items(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item

@app.get("/chests/{chest_id}/items/", response_model=list[schemas.Item])
async def get_items_in_chest(chest_id: int, db: Session = Depends(get_db)):
    items = crud.get_all_items_in_chest(db, chest_id)
    if not items:
        raise HTTPException(status_code=404, detail="No items found in the specified chest")
    
    return items
