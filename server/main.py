from typing import Union
from fastapi import FastAPI
from valheim_save_tools_py import ValheimSaveTools

app = FastAPI()

vst = ValheimSaveTools(verbose=True)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/parse_save/")
def parse_save(file_path: str = ""):
    try:
        chest_prefabs = [
            "piece_chest",
            "piece_chest_wood",
            "piece_chest_iron",
            "piece_chest_blackmetal",
            "piece_chest_stone"
        ]
        save_data = vst.to_json(file_path)

        zdoList = save_data.get("zdoList", [])

        chest_data = [zdo for zdo in zdoList if zdo.get("prefabName", "") in chest_prefabs]

        items = [chest.get('stringsByName', {}).get('items', '') for chest in chest_data]
        
        return {"status": "success", "total_chests": len(chest_data), "total_items": len(items), "items": items}
    except Exception as e:
        return {"status": "error", "message": str(e)}