from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 1. Create the SQLite Engine
# check_same_thread=False is required for SQLite in multithreaded apps like FastAPI
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI, 
    connect_args={"check_same_thread": False}
)

# 2. Create the Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Dependency Injection (Standard FastAPI pattern)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()