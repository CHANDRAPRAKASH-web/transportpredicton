
# crud.py
from sqlalchemy.orm import Session
import models, schemas

def create_transport(db: Session, transport: schemas.TransportCreate):
    db_transport = models.Transport(
        weight = transport.weight,
        volume = transport.volume,
        distance = transport.distance,
        priority = transport.priority,
        road_available = bool(transport.road_available),
        rail_available = bool(transport.rail_available),
        air_available = bool(transport.air_available),
        water_available = bool(transport.water_available),
        recommended_mode = transport.recommended_mode
    )
    db.add(db_transport)
    db.commit()
    db.refresh(db_transport)
    return db_transport

def get_transports(db: Session, skip: int = 0, limit: int = 1000):
    return db.query(models.Transport).offset(skip).limit(limit).all()

def get_transport(db: Session, transport_id: int):
    return db.query(models.Transport).filter(models.Transport.id == transport_id).first()