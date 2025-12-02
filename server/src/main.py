from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from valheim_save_tools_py import ValheimSaveTools, parse_items_from_base64
from contextlib import asynccontextmanager
from src.database import engine, get_db
from sqlalchemy.orm import Session
from collections import defaultdict
from . import schemas, crud, models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code: Initialize the database
    models.Base.metadata.create_all(bind=engine)
    yield
    # Shutdown code: (if any needed)

app = FastAPI(lifespan=lifespan)

vst = ValheimSaveTools(verbose=True)

CHEST_PREFABS = {
    "piece_chest",
    "piece_chest_wood",
    "piece_chest_iron",
    "piece_chest_blackmetal",
}


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/chests", response_model=list[schemas.Chest])
async def get_chests(db: Session = Depends(get_db)):
    chests = crud.get_all_chests(db)
    if not chests:
        raise HTTPException(status_code=404, detail="No chests found")
    
    return chests

@app.get("/items/", response_model=list[schemas.Item])
async def get_items(db: Session = Depends(get_db)):
    items = crud.get_all_items(db)
    if not items:
        raise HTTPException(status_code=404, detail="No items found")
    
    return items

@app.get("/chest/{chest_id}/items/", response_model=list[schemas.Item])
async def get_items_in_chest(chest_id: int, db: Session = Depends(get_db)):
    items = crud.get_all_items_in_chest(db, chest_id)
    if not items:
        raise HTTPException(status_code=404, detail="No items found in the specified chest")
    
    return items

@app.get("/inventory/summary/", response_model=dict[str, int])
async def get_inventory_summary(db: Session = Depends(get_db)):
    
    items: list[schemas.Item] = crud.get_all_items(db)

    if not items:
        raise HTTPException(status_code=404, detail="No items found")
    
    summary = defaultdict(int)
    for item in items:
        summary[item.name] += item.quantity
    
    if not summary:
        raise HTTPException(status_code=404, detail="No items found in inventory")
    
    return summary

@app.post("/parse_and_save/", response_model=dict)
async def parse_and_save(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a Valheim save file.")
    
    try:
        save_data = vst.to_json(file.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing save file: {str(e)}")
    
    zdoList = save_data.get("zdoList", [])

    found_chests = [zdo for zdo in zdoList if zdo.get("prefabName", "") in CHEST_PREFABS]
    total_chests = 0
    total_items = 0

    # Clear existing data (optional - remove these lines if you want to keep old data)
    db.query(models.Item).delete()
    db.query(models.Chest).delete()

    for chest_data in found_chests:
        # Extract chest data
        position = chest_data.get("position", {})
        sector = chest_data.get("sector", {})
        rotation = chest_data.get("rotation", {})
        longs = chest_data.get("longsByName", {})

        # Create chest schema for validation
        chest_create = schemas.ChestCreate(
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
        )

        # Save chest to database
        db_chest = crud.create_chest(db, chest_create)
        total_chests += 1

        # Parse items from chest
        chest_strings = chest_data.get('stringsByName', {})
        chest_items_string = chest_strings.get('items', '')
        chest_items = parse_items_from_base64(chest_items_string)
        print(chest_items)
        
        # Save each item to database
        for item_data in chest_items:
            item_create = schemas.ItemCreate(
                chest_id=db_chest.id,
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
            crud.create_item(db, item_create)
            total_items += 1
    
    return {
        "total_chests": total_chests,
        "total_items": total_items,
        "message": f"Successfully saved {total_chests} chests and {total_items} items to database"
    }
