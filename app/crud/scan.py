from sqlalchemy.orm import Session
from app.models.scan import ScanLog

def create_scan_log(db: Session, filename: str, target: str, conf: float, threat: bool):
    """Saves a scan result to the database."""
    db_obj = ScanLog(
        filename=filename,
        target_class=target,
        confidence=conf,
        is_threat=threat
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_recent_scans(db: Session, limit: int = 50):
    """Fetches the last X scans, newest first."""
    return db.query(ScanLog).order_by(ScanLog.timestamp.desc()).limit(limit).all()