from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Kinochilar API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "supersecretkey" # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI & External APIs
    AI_API_KEY: str = "sk-ws-H.IHDYEX.9Uq5.MEYCIQDIeLEv8Wq5goED9Q6zs46PT4cfyFdYPrsFdI3iGSmzLgIhAMNQeOdLsmQo50GTFDGzQ4lCwaoo0RUtIchE3bNn9E7h"
    TMDB_API_KEY: Optional[str] = "4f298c2536c4ed15f013f9c636a0fb4f"
    
    # Telegram Integration
    TELEGRAM_BOT_TOKEN: Optional[str] = "7449553755:AAH6-xY-8XmS0z6e2iE1Uj-h9fXGf9q7Ivk"
    TELEGRAM_CHANNELS: str = "@kinochi_la,@azam_televideniyesi" # List of channels to promote to

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./kinochilar.db"
    
    # Docker Environment variables (for docker-compose compatibility)
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = "password"
    POSTGRES_DB: Optional[str] = "kinochilar"
    
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
