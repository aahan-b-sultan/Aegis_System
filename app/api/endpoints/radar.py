from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.services.ai_engine import ai_engine
from app.services.virtual_radar import virtual_radar
from app.db.session import get_db
from app.crud.scan import create_scan_log, get_recent_scans
from pydantic import BaseModel

# Reporting Imports
from fastapi.responses import StreamingResponse
from app.services.report_generator import generate_pdf_report
from app.models.scan import ScanLog

router = APIRouter()

# --- SCENARIO LOADING ---

@router.post("/load-scenario/{category}")
def load_scenario(category: str):
    # FIX: Add ' _ ' to catch the 3rd value (True Label) and ignore it
    success, message, _ = virtual_radar.load_scenario(category)
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"status": "Scenario Loaded", "details": message}

@router.post("/load-random")
def load_random():
    # FIX: Add ' _ ' here too
    success, message, _ = virtual_radar.load_random_scenario()
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"status": "Random Scenario Loaded", "details": message}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        # FIX: Add ' _ ' here too
        success, message, _ = virtual_radar.inject_external_data(contents, file.filename)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"status": "External Data Injected", "details": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- SCANNING ---

@router.get("/scan")
def perform_scan(db: Session = Depends(get_db)):
    # 1. Get Data
    raw_matrix = virtual_radar.get_next_frame()
    if raw_matrix is None:
        raise HTTPException(status_code=400, detail="Radar offline.")

    # 2. AI Analysis
    result = ai_engine.predict(raw_matrix)

    # 3. LOG TO DATABASE
    create_scan_log(
        db=db,
        filename=virtual_radar.get_current_filename(),
        target=result["label"],
        conf=result["confidence"],
        threat=result["is_threat"]
    )

    # 4. Return JSON
    return {
        "status": "Scan Complete",
        "target_class": result["label"],
        "confidence": result["confidence"],
        "is_threat": result["is_threat"],
        "heatmap_data": raw_matrix.tolist() 
    }

# --- HISTORY & REPORTING ---

@router.get("/history")
def read_history(db: Session = Depends(get_db)):
    return get_recent_scans(db)

@router.get("/report/{scan_id}")
def download_report(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(ScanLog).filter(ScanLog.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan log not found")

    pdf_buffer = generate_pdf_report(scan)
    date_str = scan.timestamp.strftime('%Y%m%d')
    filename = f"AEGIS_Report_{scan.target_class}_{date_str}_{scan_id}.pdf"
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- FEEDBACK & ANALYTICS ---

class FeedbackRequest(BaseModel):
    scan_id: int
    correct_label: str

@router.put("/feedback")
def submit_feedback(feedback: FeedbackRequest, db: Session = Depends(get_db)):
    log = db.query(ScanLog).filter(ScanLog.id == feedback.scan_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    log.user_verified = True
    log.corrected_label = feedback.correct_label
    db.commit()
    return {"status": "verified"}

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    logs = db.query(ScanLog).all()
    stats = {
        "total": len(logs),
        "threats": 0,
        "class_counts": {"DRONE": 0, "CAR": 0, "HUMAN": 0, "UNKNOWN": 0}
    }
    for log in logs:
        if log.is_threat:
            stats["threats"] += 1
        label = log.corrected_label if log.user_verified else log.target_class
        label = label.upper()
        if label in stats["class_counts"]:
            stats["class_counts"][label] += 1
        else:
            stats["class_counts"]["UNKNOWN"] += 1     
    return stats