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

class ParseSaveResponse(BaseModel):
    status: str
    total_chests: int
    total_items: int
    items: list[Item]

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
async def parse_save(file: UploadFile = File(...)) -> ParseSaveResponse:
    try:
        if file.content_type != "application/octet-stream":
            return ErrorResponse(status="error", message="Invalid file type. Please upload a Valheim save file.")
        
        if file.filename in DB:
            saved_data = DB[file.filename]
            return ParseSaveResponse(
                status="success",
                total_chests=saved_data["total_chests"],
                total_items=saved_data["total_items"],
                items=saved_data["items"]
            )
        
        save_data = vst.to_json(file.file)
        zdoList = save_data.get("zdoList", [])

        chest_data = [zdo for zdo in zdoList if zdo.get("prefabName", "") in CHEST_PREFABS]

        items = []

        for chest in chest_data:
            chestStringByName = chest.get('stringsByName', {})
            chestItemsString = chestStringByName.get('items', '')
            chest_items = parse_items_from_base64(chestItemsString)
            items.extend(chest_items)
        
        DB[file.filename] = {
            "total_chests": len(chest_data),
            "total_items": len(items),
            "items": items
        }
        
        return ParseSaveResponse(status="success", total_chests=len(chest_data), total_items=len(items), items=items)
    except Exception as e:
        return ErrorResponse(status="error", message=str(e))