from pydantic import BaseModel
from datetime import datetime


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
