from sqlalchemy.orm import Session
from typing import Optional
from App.models import User
from ..schemas import UserCreate
from ..core.auth import get_password_hash
from ..core.config import settings
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

# --- READ --- #

def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """Get user by ID - reads from primary DB only"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email - reads from primary DB only"""
    return db.query(User).filter(User.email == email).first()


# --- CREATE --- #

def create_user(
    local_db: Session, 
    supabase_db: Optional[Session], 
    user: UserCreate
) -> User:
    """Create user with SAME ID in both databases if needed"""
    hashed_password = get_password_hash(user.password)

    # Create local first if needed
    local_user = None
    if settings.DB_MODE in ("local", "both"):
        local_user = User(
            name=user.name,
            age=user.age,
            email=user.email,
            hashed_password=hashed_password
        )
        local_db.add(local_user)
        local_db.commit()
        local_db.refresh(local_user)

    # Create Supabase if needed
    if settings.DB_MODE in ("supabase", "both") and supabase_db:
        try:
            supabase_user = User(
                id=local_user.id if local_user else None,  # use same ID if local exists
                name=user.name,
                age=user.age,
                email=user.email,
                hashed_password=hashed_password
            )
            supabase_db.add(supabase_user)
            supabase_db.commit()
        except Exception as e:
            logger.error(f"Supabase create failed: {e}")
            if settings.SUPABASE_FAILURE_STRATEGY == "fail" and local_user:
                local_db.rollback()
                raise

    return local_user if local_user else supabase_user


# --- UPDATE --- #

def update_user(
    local_db: Session,
    supabase_db: Optional[Session],
    user_id: UUID,
    user: UserCreate
) -> Optional[User]:
    """Update user in relevant database(s)"""
    updated_user = None

    dbs = []
    if settings.DB_MODE in ("local", "both"):
        dbs.append(local_db)
    if settings.DB_MODE in ("supabase", "both"):
        dbs.append(supabase_db)

    for db in dbs:
        if not db:
            continue
        try:
            db_user = db.query(User).filter(User.id == user_id).first()
            if db_user:
                db_user.name = user.name
                db_user.age = user.age
                db_user.email = user.email
                db.commit()
                db.refresh(db_user)
                if not updated_user:
                    updated_user = db_user
        except Exception as e:
            logger.error(f"Update failed on {db}: {e}")
            if settings.SUPABASE_FAILURE_STRATEGY == "fail" and db != local_db:
                local_db.rollback()
                raise

    return updated_user


# --- DELETE --- #

def delete_user(
    local_db: Session,
    supabase_db: Optional[Session],
    user_id: UUID
) -> bool:
    """Delete user from relevant database(s)"""
    success = False

    dbs = []
    if settings.DB_MODE in ("local", "both"):
        dbs.append(local_db)
    if settings.DB_MODE in ("supabase", "both"):
        dbs.append(supabase_db)

    for db in dbs:
        if not db:
            continue
        try:
            db_user = db.query(User).filter(User.id == user_id).first()
            if db_user:
                db.delete(db_user)
                db.commit()
                success = True
        except Exception as e:
            logger.error(f"Delete failed on {db}: {e}")

    return success
