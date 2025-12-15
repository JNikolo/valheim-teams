from pydantic import BaseModel
from typing import Union


# ************************ Item Schema *************************** #
class ItemBase(BaseModel):
    name: str
    quantity: int
    quality: int
    durability: int
    position_x: int
    position_y: int
    equipped: bool
    variant: int
    crafter_id: int
    crafter_name: Union[str, None]
    chest_id: int


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int

    model_config = {"from_attributes": True}
