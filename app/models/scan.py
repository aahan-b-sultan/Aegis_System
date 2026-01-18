from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.session import Base

Base = declarative_base()

class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    # Use datetime.now so logs match your laptop time
    timestamp = Column(DateTime, default=datetime.now) 
    filename = Column(String, index=True)
    target_class = Column(String)
    confidence = Column(Float)
    is_threat = Column(Boolean, default=False)