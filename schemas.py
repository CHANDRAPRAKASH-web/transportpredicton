# schemas.py
from pydantic import BaseModel
from typing import Optional

class TransportBase(BaseModel):
    weight: int
    volume: int
    distance: int
    priority: int
    road_available: int
    rail_available: int
    air_available: int
    water_available: int
    recommended_mode: Optional[str] = None  # optional during create

class TransportCreate(TransportBase):
    pass

class Transport(TransportBase):
    id: int

    class Config:
        orm_mode = True
