from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from app.db.session import Base

class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    filename = Column(String, index=True)
    target_class = Column(String)
    confidence = Column(Float)
    is_threat = Column(Boolean, default=False)
    
    # --- NEW COLUMNS FOR FEEDBACK ---
    user_verified = Column(Boolean, default=False)
    corrected_label = Column(String, nullable=True)