from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Ludix API"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Database settings (PostgreSQL via Supabase)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ludix_app.db")  # Fallback a SQLite
    
    # Security settings
    SECRET_KEY: str = "ludix-super-secret-key-for-development-only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # External services
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # Email settings (for notifications)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar campos extra

# Create settings instance
settings = Settings()

# CORS origins (defined separately to avoid pydantic issues)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://192.168.0.12:3000",
    "http://192.168.0.12:3001",
    "http://172.19.0.1:3000",
    "http://172.19.0.1:3001",
    "http://172.18.0.1:3000",
    "http://172.18.0.1:3001"
]
