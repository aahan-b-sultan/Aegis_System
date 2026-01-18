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
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_PATH: str = os.path.join(BASE_DIR, "ai_models/radar_model.h5") # Adjusted path slightly for Docker safety
    LABEL_ENCODER_PATH: str = os.path.join(BASE_DIR, "ai_models/label_encoder.pkl")
    
    # Database Path Logic
    # If inside Docker (we mapped /app/db_storage), use that. Else use local folder.
    if os.path.exists("/app/db_storage"):
        SQLALCHEMY_DATABASE_URI: str = "sqlite:////app/db_storage/aegis.db"
    else:
        SQLALCHEMY_DATABASE_URI: str = "sqlite:///./aegis.db"

settings = Settings()