import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aegis Radar Surveillance"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Paths
    # 1. Get the path of this file
    _current_file = os.path.abspath(__file__)
    # 2. Go up 3 levels to reach Project Root
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(_current_file)))
    
    # Paths to Models
    MODEL_PATH: str = os.path.join(BASE_DIR, "ai_models", "radar_model.h5")
    LABEL_ENCODER_PATH: str = os.path.join(BASE_DIR, "ai_models", "label_encoder.pkl")
    
    # --- DOCKER AWARE DATABASE LOGIC ---
    # Inside Docker, we map a volume to /app/db_storage
    if os.path.exists("/app/db_storage"):
        # We are in Docker
        SQLALCHEMY_DATABASE_URI: str = "sqlite:////app/aegis.db"
    else:
        # We are on local laptop
        SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{os.path.join(BASE_DIR, 'aegis.db')}"

settings = Settings()