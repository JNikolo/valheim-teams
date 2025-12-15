from pydantic import BaseModel


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
