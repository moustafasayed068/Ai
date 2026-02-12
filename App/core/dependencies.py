from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from App.db.session import get_db
from .auth import decode_access_token


http_bearer = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer), 
    db: Session = Depends(get_db)
):
    """Get current user from primary database based on DB_MODE"""
    from ..repositories.repository import get_user_by_email
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # Get user from PRIMARY database (based on DB_MODE)
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    
    return user