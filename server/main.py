from typing import Union
from fastapi import FastAPI, File, UploadFile
from valheim_save_tools_py import ValheimSaveTools, parse_items_from_base64
from pydantic import BaseModel

app = FastAPI()

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
class ParseSaveResponse(BaseModel):
    status: str
    total_chests: int
    total_items: int
    items: list[Item] = []
    chests: list[Chest] = []

class ErrorResponse(BaseModel):
    status: str
    message: str

DB = {}

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/parse_save/")
async def parse_save(file: UploadFile = File(...)) -> Union[ParseSaveResponse, ErrorResponse]:
    try:
        if file.content_type != "application/octet-stream":
            return ErrorResponse(
                status="error",
                message="Invalid file type. Please upload a Valheim save file."
            )
        
        if file.filename in DB:
            saved_data = DB[file.filename]
            return ParseSaveResponse(
                status="success",
                total_chests=saved_data["total_chests"],
                total_items=saved_data["total_items"],
                items=saved_data["items"],
                chests=saved_data["chests"]
            )

        save_data = vst.to_json(file.file)
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
        
        DB[file.filename] = {
            "total_chests": len(parsed_chests),
            "chests": parsed_chests,
            "total_items": len(parsed_items),
            "items": parsed_items
        }
        
        return ParseSaveResponse(
            status="success", 
            total_chests=len(parsed_chests), 
            total_items=len(parsed_items), 
            items=parsed_items, 
            chests=parsed_chests
        )
    except Exception as e:
        return ErrorResponse(status="error", message=str(e))