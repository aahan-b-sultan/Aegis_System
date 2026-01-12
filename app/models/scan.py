from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now) # Uses Your Laptop time
    filename = Column(String)
    target_class = Column(String)
    confidence = Column(Float)
    is_threat = Column(Boolean, default=False)