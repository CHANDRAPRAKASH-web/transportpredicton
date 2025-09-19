
# models.py
from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Transport(Base):
    __tablename__ = "transports"

    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Integer, nullable=False)
    volume = Column(Integer, nullable=False)
    distance = Column(Integer, nullable=False)
    priority = Column(Integer, nullable=False)
    road_available = Column(Boolean, default=False)
    rail_available = Column(Boolean, default=False)
    air_available = Column(Boolean, default=False)
    water_available = Column(Boolean, default=False)
    recommended_mode = Column(String, nullable=True)