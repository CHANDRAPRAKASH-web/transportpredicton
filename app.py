# app.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, schemas, crud
from ml_model import predict_mode_with_reason
from typing import List

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Transport API (preserve endpoints + advanced predict)")

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Transport API is up"}

# -------------------------
# Add transport (unchanged behaviour)
# -------------------------
@app.post("/add-transport", response_model=schemas.Transport)
def add_transport(transport: schemas.TransportCreate, db: Session = Depends(get_db)):
    """
    Add a transport record.
    Accepts JSON in body with the same fields you used before (weight, volume, distance, priority,
    road_available, rail_available, air_available, water_available, optional recommended_mode).
    """
    return crud.create_transport(db, transport)

# -------------------------
# Get all transports (unchanged behaviour)
# -------------------------
@app.get("/get-transports", response_model=List[schemas.Transport])
def get_transports(db: Session = Depends(get_db)):
    return crud.get_transports(db)

# -------------------------
# Predict (KEEP rectangle query inputs exactly as before)
# -------------------------
@app.post("/predict")
def predict(
    weight: int,
    volume: int,
    distance: int,
    priority: int,
    road_available: int,
    rail_available: int,
    air_available: int,
    water_available: int
):
    """
    Predict recommended mode and return justification + comparison.
    Inputs are query parameters (the rectangular boxes in Swagger) — unchanged.
    """
    try:
        recommended, reasons, comparison = predict_mode_with_reason(
            weight, volume, distance, priority,
            road_available, rail_available, air_available, water_available
        )

        return {
            "recommended_mode": recommended,
            "justification": reasons,
            "comparison": comparison
        }
    except Exception as e:
        # return a clear error message for debugging rather than 500 silence
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
