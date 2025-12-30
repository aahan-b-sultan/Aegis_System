from fastapi import APIRouter, HTTPException
from app.services.ai_engine import ai_engine
from app.services.virtual_radar import virtual_radar
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Schema for response (Professional Data Contract)
class RadarResponse(BaseModel):
    status: str
    target_class: Optional[str] = None
    confidence: Optional[float] = None
    is_threat: bool = False
    heatmap_data: Optional[List[List[float]]] = None # Sending matrix to UI

@router.post("/load-scenario/{category}")
def load_scenario(category: str):
    """
    Simulates pointing the radar at a specific target type.
    Categories: 'drone', 'human', 'car'
    """
    success, message = virtual_radar.load_scenario(category)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"status": "Scenario Loaded", "details": message}

@router.get("/scan", response_model=RadarResponse)
def perform_scan():
    """
    Triggers a single scan frame from the virtual radar and analyzes it.
    """
    # 1. Get Data from Virtual Sensor
    raw_matrix = virtual_radar.get_next_frame()
    
    if raw_matrix is None:
        raise HTTPException(status_code=400, detail="Radar offline or no scenario loaded.")

    # 2. Analyze with AI
    result = ai_engine.predict(raw_matrix)

    # 3. Return JSON to Frontend
    return {
        "status": "Scan Complete",
        "target_class": result["label"],
        "confidence": result["confidence"],
        "is_threat": result["is_threat"],
        # Convert numpy array to list for JSON serialization
        "heatmap_data": raw_matrix.tolist() 
    }

@router.post("/load-random")
def load_random():
    """
    Injects a random signal for blind testing.
    """
    success, message, true_label = virtual_radar.load_random_scenario()
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    # We return the message "INTERCEPTING..." 
    # We DO NOT return the true_label yet, to keep the suspense!
    return {"status": "Random Scenario Loaded", "details": message}