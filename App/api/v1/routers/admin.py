from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Literal
from ....core.config import settings
from App.db.session import engine, supabase_engine
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class DBModeUpdate(BaseModel):
    db_mode: Literal["local", "supabase", "both"]
    failure_strategy: Literal["fail", "continue", "retry"] = "continue"

class DBStatusResponse(BaseModel):
    current_mode: str
    failure_strategy: str
    local_db_connected: bool
    supabase_db_connected: bool
    local_db_url: str
    supabase_db_url: str | None

@router.get("/db-status", response_model=DBStatusResponse)
def get_database_status():
    """
    Get current database configuration and connection status
    """
    local_connected = False
    supabase_connected = False
    
    # Test local connection
    try:
        with engine.connect() as conn:
            local_connected = True
    except Exception as e:
        logger.error(f"Local DB connection failed: {e}")
    
    # Test Supabase connection
    if supabase_engine:
        try:
            with supabase_engine.connect() as conn:
                supabase_connected = True
        except Exception as e:
            logger.error(f"Supabase DB connection failed: {e}")
    
    # Mask passwords in URLs
    def mask_password(url: str) -> str:
        if not url:
            return url
        parts = url.split('@')
        if len(parts) > 1:
            credentials = parts[0].split('://')
            if len(credentials) > 1:
                user_pass = credentials[1].split(':')
                if len(user_pass) > 1:
                    return f"{credentials[0]}://{user_pass[0]}:****@{parts[1]}"
        return url
    
    return DBStatusResponse(
        current_mode=settings.DB_MODE,
        failure_strategy=settings.SUPABASE_FAILURE_STRATEGY,
        local_db_connected=local_connected,
        supabase_db_connected=supabase_connected,
        local_db_url=mask_password(settings.DATABASE_URL),
        supabase_db_url=mask_password(settings.SUPABASE_DB_URL) if settings.SUPABASE_DB_URL else None
    )

@router.post("/db-mode", response_model=dict)
def update_database_mode(config: DBModeUpdate):
    """
    Update database mode at runtime
    
    WARNING: This changes the global configuration. 
    Use with caution in production environments.
    """
    # Validate mode
    if config.db_mode in ["supabase", "both"] and not settings.SUPABASE_DB_URL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot set DB_MODE to '{config.db_mode}' - SUPABASE_DB_URL is not configured"
        )
    
    if config.db_mode in ["supabase", "both"] and not supabase_engine:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot set DB_MODE to '{config.db_mode}' - Supabase engine is not initialized"
        )
    
    # Update settings
    old_mode = settings.DB_MODE
    old_strategy = settings.SUPABASE_FAILURE_STRATEGY
    
    settings.DB_MODE = config.db_mode
    settings.SUPABASE_FAILURE_STRATEGY = config.failure_strategy
    
    logger.info(f"Database mode changed: {old_mode} -> {config.db_mode}")
    logger.info(f"Failure strategy changed: {old_strategy} -> {config.failure_strategy}")
    
    return {
        "message": "Database configuration updated successfully",
        "previous_mode": old_mode,
        "new_mode": config.db_mode,
        "previous_strategy": old_strategy,
        "new_strategy": config.failure_strategy
    }
