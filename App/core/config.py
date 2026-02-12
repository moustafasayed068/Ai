from pydantic_settings import BaseSettings
from typing import Optional, Literal

class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_DB_URL: Optional[str] = None
    
    DB_MODE: Literal["local", "supabase", "both"] = "local"
    SUPABASE_FAILURE_STRATEGY: Literal["fail", "continue", "retry"] = "continue"
    
    COHERE_API_KEY: str  
    
    
    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"

settings = Settings()
COHERE_API_KEY = settings.COHERE_API_KEY  



SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS