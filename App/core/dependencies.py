from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from App.db.session import get_db
from .auth import decode_access_token


http_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db)
):
    """Get current user from primary database based on DB_MODE"""
    from ..repositories.user import get_user_by_email

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = await decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # Get user from PRIMARY database (based on DB_MODE)
    user = await get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    return user


async def require_admin(current_user=Depends(get_current_user)):
    """Allow only users whose email is listed in ADMIN_EMAILS."""
    from .config import settings

    admins = {e.strip().lower() for e in settings.ADMIN_EMAILS.split(",") if e.strip()}
    if current_user.email.lower() not in admins:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
