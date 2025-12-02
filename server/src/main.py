from typing import Union
from fastapi import FastAPI, File, UploadFile, HTTPException
from valheim_save_tools_py import ValheimSaveTools, parse_items_from_base64
from pydantic import BaseModel
from contextlib import asynccontextmanager
from src.database import engine
from src.models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code: Initialize the database
    Base.metadata.create_all(bind=engine)
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

class Item(BaseModel):
    name: str
    stack: int
    quality: int
    durability: float
    pos_x: int
    pos_y: int
    equipped: bool
    variant: int
    crafter_id: int = 0
    crafter_name: Union[str, None] = None
    chest_id: int = 0

class Rotation(BaseModel):
    x: float
    y: float
    z: float

class Position(BaseModel):
    x: float
    y: float
    z: float

class Sector(BaseModel):
    x: int
    y: int

class Chest(BaseModel):
    chest_id: int
    chest_type: str
    position: Position
    sector: Sector
    rotation: Rotation
    creator_id: int

DB = {}

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/chests")
async def get_chests():
    chests = DB.get("chests", [])
    if not chests:
        raise HTTPException(status_code=404, detail="No chests found")
    
    return {"success": True, "chests": chests, "count": len(chests)}

@app.get("/items/")
async def get_items():
    items = DB.get("items", [])
    if not items:
        raise HTTPException(status_code=404, detail="No items found")
    
    return {"success": True, "items": items, "count": len(items)}

@app.get("/chest/{chest_id}/items/")
async def get_items_in_chest(chest_id: int):
    items = DB.get("items", [])
    chest_items = [item for item in items if item["chest_id"] == chest_id]
    if not chest_items:
        raise HTTPException(status_code=404, detail="No items found in the specified chest")
    
    return {"success": True, "items": chest_items, "count": len(chest_items)}

@app.get("/inventory/summary/")
async def get_inventory_summary():
    count_chests = len(DB.get("chests", []))
    items = DB.get("items", [])

    if count_chests == 0:
        raise HTTPException(status_code=404, detail="No chests found")
    if not items:
        raise HTTPException(status_code=404, detail="No items found")
    
    summary = {}
    for item in items:
        if item["name"] in summary:
            summary[item["name"]] += item["stack"]
        else:
            summary[item["name"]] = item["stack"]
    
    if not summary:
        raise HTTPException(status_code=404, detail="No items found in inventory")
    
    return {"success": True, "summary": summary, "total_chests": count_chests, "total_items": len(items)}

@app.post("/parse_and_save/")
async def parse_and_save(file: UploadFile = File(...)):
    global DB
    if file.content_type != "application/octet-stream":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a Valheim save file.")
        
    try:
        save_data = vst.to_json(file.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing save file: {str(e)}")
    
    zdoList = save_data.get("zdoList", [])

    found_chests = [zdo for zdo in zdoList if zdo.get("prefabName", "") in CHEST_PREFABS]
    parsed_items = []
    parsed_chests = []

    for chest_id, chest_data in enumerate(found_chests):
        chest: Chest = {}
        chest["chest_id"] = chest_id
        chest["chest_type"] = chest_data.get("prefabName", "")
        chest["position"] = chest_data.get("position", {})
        chest["sector"] = chest_data.get("sector", {})
        chest["rotation"] = chest_data.get("rotation", {})
        longs= chest_data.get("longsByName", {})
        chest["creator_id"] = longs.get("creator", "")

        parsed_chests.append(chest)


        chestStringByName = chest_data.get('stringsByName', {})
        chestItemsString = chestStringByName.get('items', '')
        chest_items: list[Item] = parse_items_from_base64(chestItemsString)
        
        for item in chest_items:
            item["chest_id"] = chest_id

        parsed_items.extend(chest_items)
    
    DB = {
        "total_chests": len(parsed_chests),
        "chests": parsed_chests,
        "total_items": len(parsed_items),
        "items": parsed_items
    }
    
    return {
        "status": True,
        "total_chests": len(parsed_chests),
        "total_items": len(parsed_items),
    }
