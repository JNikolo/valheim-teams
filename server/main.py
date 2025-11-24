from typing import Union
from fastapi import FastAPI
from valheim_save_tools_py import ValheimSaveTools, parse_items_from_base64

app = FastAPI()

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


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/parse_save/")
def parse_save(file_path: str = ""):
    try:
        save_data = vst.to_json(file_path)

        zdoList = save_data.get("zdoList", [])

        chest_data = [zdo for zdo in zdoList if zdo.get("prefabName", "") in CHEST_PREFABS]

        items = []

        for chest in chest_data:
            chestStringByName = chest.get('stringsByName', {})
            chestItemsString = chestStringByName.get('items', '')
            chest_items = parse_items_from_base64(chestItemsString)
            items.append(chest_items)
        
        return {"status": "success", "total_chests": len(chest_data), "total_items": len(items), "items": items}
    except Exception as e:
        return {"status": "error", "message": str(e)}