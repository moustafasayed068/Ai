"""
Database Service Layer
Handles intelligent routing between local and Supabase databases based on DB_MODE
"""
from sqlalchemy.orm import Session
from typing import Optional, TypeVar, Callable
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)    

T = TypeVar('T')

class DatabaseService:
    """Service to handle database operations based on configuration"""
    
    @staticmethod
    def execute_operation(
        operation: Callable[[Session], T],
        local_db: Session,
        supabase_db: Optional[Session] = None,
        operation_name: str = "database operation"
    ) -> T:
        """
        Execute a database operation according to DB_MODE settings
        
        Args:
            operation: Function that takes a Session and returns a result
            local_db: Local database session
            supabase_db: Supabase database session (optional)
            operation_name: Description of the operation for logging
            
        Returns:
            Result of the operation
        """
        
        if settings.DB_MODE == "local":
            return DatabaseService._execute_local(operation, local_db, operation_name)
        
        elif settings.DB_MODE == "supabase":
            if supabase_db is None:
                raise ValueError("Supabase DB session required when DB_MODE='supabase'")
            return DatabaseService._execute_supabase(operation, supabase_db, operation_name)
        
        elif settings.DB_MODE == "both":
            if supabase_db is None:
                raise ValueError("Supabase DB session required when DB_MODE='both'")
            return DatabaseService._execute_both(operation, local_db, supabase_db, operation_name)
        
        else:
            raise ValueError(f"Invalid DB_MODE: {settings.DB_MODE}")
    
    @staticmethod
    def _execute_local(operation: Callable[[Session], T], db: Session, operation_name: str) -> T:
        """Execute operation on local DB only"""
        try:
            result = operation(db)
            logger.debug(f"[LOCAL] {operation_name} completed successfully")
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"[LOCAL] {operation_name} failed: {e}")
            raise
    
    @staticmethod
    def _execute_supabase(operation: Callable[[Session], T], db: Session, operation_name: str) -> T:
        """Execute operation on Supabase DB only"""
        try:
            result = operation(db)
            logger.debug(f"[SUPABASE] {operation_name} completed successfully")
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"[SUPABASE] {operation_name} failed: {e}")
            raise
    
    @staticmethod
    def _execute_both(
        operation: Callable[[Session], T], 
        local_db: Session, 
        supabase_db: Session, 
        operation_name: str
    ) -> T:
        """Execute operation on both databases with configurable failure handling"""
        local_result = None
        supabase_success = False
        
        try:
            # Execute on local DB first (primary)
            local_result = operation(local_db)
            logger.debug(f"[LOCAL] {operation_name} completed successfully")
            
            # Try Supabase
            try:
                operation(supabase_db)
                supabase_success = True
                logger.debug(f"[SUPABASE] {operation_name} completed successfully")
            except Exception as supabase_error:
                logger.error(f"[SUPABASE] {operation_name} failed: {supabase_error}")
                
                if settings.SUPABASE_FAILURE_STRATEGY == "fail":
                    # Rollback local and fail
                    local_db.rollback()
                    supabase_db.rollback()
                    raise Exception(f"Supabase operation failed: {supabase_error}")
                
                elif settings.SUPABASE_FAILURE_STRATEGY == "retry":
                    # Retry once
                    try:
                        logger.info(f"[SUPABASE] Retrying {operation_name}...")
                        operation(supabase_db)
                        supabase_success = True
                        logger.info(f"[SUPABASE] {operation_name} succeeded on retry")
                    except Exception as retry_error:
                        logger.error(f"[SUPABASE] Retry failed: {retry_error}")
                        supabase_db.rollback()
                        if settings.SUPABASE_FAILURE_STRATEGY == "fail":
                            local_db.rollback()
                            raise
                        logger.warning(f"[BOTH] Continuing with local DB only")
                
                elif settings.SUPABASE_FAILURE_STRATEGY == "continue":
                    # Continue with local only
                    supabase_db.rollback()
                    logger.warning(f"[BOTH] {operation_name} completed on local only (Supabase failed)")
            
            return local_result
            
        except Exception as e:
            local_db.rollback()
            if supabase_db:
                supabase_db.rollback()
            logger.error(f"[BOTH] {operation_name} failed: {e}")
            raise

# Convenience function
def execute_db_operation(
    operation: Callable[[Session], T],
    local_db: Session,
    supabase_db: Optional[Session] = None,
    operation_name: str = "operation"
) -> T:
    """Wrapper function for DatabaseService.execute_operation"""
    return DatabaseService.execute_operation(operation, local_db, supabase_db, operation_name)