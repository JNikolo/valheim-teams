from pydantic import BaseModel
from typing import Union, Optional
from datetime import datetime

#============================== Schemas ============================== #
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

# ************************ Chest Schema *************************** #
class ChestBase(BaseModel):
    prefab_name: str
    position_x: float
    position_y: float
    position_z: float
    sector_x: int
    sector_y: int
    rotation_x: float
    rotation_y: float
    rotation_z: float
    creator_id: int
    world_id: int

class ChestCreate(ChestBase):
    pass

class Chest(ChestBase):
    id: int

    model_config = {"from_attributes": True}

# ************************ World Schema *************************** #
class WorldBase(BaseModel):
    uid: int
    version: int
    net_time: float
    modified_time: int
    name: str
    seed: int
    seed_name: str
    
class WorldCreate(WorldBase):
    pass

class World(WorldBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
    
# ============================== End Schemas ============================== #