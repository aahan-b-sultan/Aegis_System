from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    filename = Column(String)
    detected_class = Column(String)
    confidence = Column(Float)
    is_threat = Column(Boolean, default=False)
    raw_data_path = Column(String, nullable=True) # Path to stored CSV