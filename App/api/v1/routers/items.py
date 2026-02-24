from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....repositories.item import (
    create_item, get_item,
    get_items_by_user, update_item, delete_item
)
from ....schemas import ItemCreate, ItemResponse
from ....db.session import get_db, get_supabase_db
from ....core.dependencies import get_current_user
from ....core.config import settings
from ....schemas import UserResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item_endpoint(
    item: ItemCreate,
    db: Session = Depends(get_db),
    supabase_db: Optional[Session] = Depends(get_supabase_db) if settings.DB_MODE in ["supabase", "both"] else None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new item.
    SECURE: Users can only create items for themselves.
    """
    if current_user.id != item.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create items for yourself"
        )

    try:
        return await create_item(db, supabase_db, item)
    except Exception as e:
        logger.error(f"Failed to create item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create item: {str(e)}"
        )


@router.get("/", response_model=List[ItemResponse])
async def read_my_items(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all items for the current authenticated user.
    SECURE: Returns only current user's items.
    """
    return await get_items_by_user(db, current_user.id)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item_endpoint(
    item_id: int,
    item: ItemCreate,
    db: Session = Depends(get_db),
    supabase_db: Optional[Session] = Depends(get_supabase_db) if settings.DB_MODE in ["supabase", "both"] else None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update item.
    SECURE: Users can only update their own items.
    """
    db_item = await get_item(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    if db_item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own items"
        )

    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot transfer item ownership"
        )

    try:
        updated_item = await update_item(db, supabase_db, item_id, item)
        if not updated_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_endpoint(
    item_id: int,
    db: Session = Depends(get_db),
    supabase_db: Optional[Session] = Depends(get_supabase_db) if settings.DB_MODE in ["supabase", "both"] else None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete item.
    SECURE: Users can only delete their own items.
    """
    db_item = await get_item(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    if db_item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own items"
        )

    try:
        deleted = await delete_item(db, supabase_db, item_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )