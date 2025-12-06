"""
Core configuration for Hanco-AI Backend
Environment variables, settings, constants
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses lru_cache for singleton pattern.
    """
    
    # ==================== App Settings ====================
    PROJECT_NAME: str = "Hanco AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # ==================== API Settings ====================
    API_V1_PREFIX: str = "/api/v1"
    
    # ==================== Firebase Configuration ====================
    FIREBASE_CREDENTIALS_PATH: str = Field(
        default=r"C:\Users\altaf\Desktop\HANCO\hanco-ai-firebase-adminsdk-fbsvc-db35697dfc.json",
        env="FIREBASE_CREDENTIALS_PATH"
    )
    FIREBASE_PROJECT_ID: str = Field(default="hanco-ai", env="FIREBASE_PROJECT_ID")
    
    # Firebase Web Config (for frontend reference)
    FIREBASE_API_KEY: str = Field(default="AIzaSyBYPFJAUEYBkz8FI-kwUdL9FQpi3tVpYvE", env="FIREBASE_API_KEY")
    FIREBASE_AUTH_DOMAIN: str = Field(default="hanco-ai.firebaseapp.com", env="FIREBASE_AUTH_DOMAIN")
    FIREBASE_STORAGE_BUCKET: str = Field(default="hanco-ai.firebasestorage.app", env="FIREBASE_STORAGE_BUCKET")
    FIREBASE_MESSAGING_SENDER_ID: str = Field(default="433704594962", env="FIREBASE_MESSAGING_SENDER_ID")
    FIREBASE_APP_ID: str = Field(default="1:433704594962:web:767ae6989e11a989bc32cb", env="FIREBASE_APP_ID")
    FIREBASE_MEASUREMENT_ID: str = Field(default="G-Q68Z3GV126", env="FIREBASE_MEASUREMENT_ID")
    
    # ==================== AI Services ====================
    GEMINI_API_KEY: str = Field(default="AIzaSyD0SIPE9uyxoTGHl-D6_KKLjsp1bcDJFLw", env="GEMINI_API_KEY")
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")  # Fallback
    
    # ==================== Weather Service ====================
    OPEN_METEO_URL: str = Field(default="https://api.open-meteo.com/v1/forecast", env="OPEN_METEO_URL")
    
    # ==================== ML Model ====================
    ONNX_MODEL_PATH: str = Field(default="./ml/models/model.onnx", env="ONNX_MODEL_PATH")
    
    # ==================== Frontend & CORS ====================
    FRONTEND_URL: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://hanco-ai.web.app",
        "https://hanco-ai.firebaseapp.com",
    ]
    
    # ==================== Crawl4AI Settings ====================
    SCRAPING_ENABLED: bool = Field(default=True, env="SCRAPING_ENABLED")
    SCRAPING_INTERVAL_HOURS: int = Field(default=24, env="SCRAPING_INTERVAL_HOURS")
    
    # ==================== Logging ====================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # ==================== Rate Limiting ====================
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance (singleton pattern).
    Uses lru_cache to ensure only one instance is created.
    """
    return Settings()


# Global settings instance
settings = get_settings()
