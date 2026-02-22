from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from ....repositories.user import (
    create_user, get_user, get_user_by_email, 
    update_user, delete_user
)
from ....schemas import UserCreate, UserResponse, Token
from ....core.auth import create_access_token, create_refresh_token
from ....core.dependencies import get_current_user
from ....db.session import get_db, get_supabase_db
from ....core.config import settings
import logging
from uuid import UUID

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user: UserCreate,
    db: Session = Depends(get_db),
    supabase_db: Optional[Session] = Depends(get_supabase_db) if settings.DB_MODE in ["supabase", "both"] else None
):
    """Create a new user - PUBLIC endpoint (no auth required)"""
    # Check if email already exists
    existing = get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    
    try:
        return create_user(db, supabase_db, user)
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/authenticate/{user_id}", response_model=Token)
def authenticate(user_id: UUID, db: Session = Depends(get_db)):
    """
    Generate access and refresh tokens for a user
    WARNING: This is for testing only - in production, require password!
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user's information
    SECURE: Users can only see their own info
    """
    return current_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user_endpoint(
    user_id: int, 
    user: UserCreate, 
    db: Session = Depends(get_db), 
    supabase_db: Optional[Session] = Depends(get_supabase_db) if settings.DB_MODE in ["supabase", "both"] else None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user
    SECURITY FIX: Users can only update their own profile
    """
    # Check if user is trying to update their own profile
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    try:
        updated_user = update_user(db, supabase_db, user_id, user)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )
        return updated_user
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    user_id: UUID, 
    db: Session = Depends(get_db),
    supabase_db: Optional[Session] = Depends(get_supabase_db) if settings.DB_MODE in ["supabase", "both"] else None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete user
    SECURITY FIX: Users can only delete their own account
    """
    # Check if user is trying to delete their own account
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account"
        )
    
    try:
        deleted = delete_user(db, supabase_db, user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )