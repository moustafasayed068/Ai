from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ....repositories.repository import get_user, create_item, get_item, get_items_by_user
from ....schemas import ItemCreate, ItemResponse
from ....core.database import get_db

router = APIRouter()

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item_endpoint(item: ItemCreate, db: Session = Depends(get_db)):
    # ensure owner exists
    db_user = get_user(db, item.owner_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Owner (user) not found")
    return create_item(db, item)


@router.get("/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.get("/user/{user_id}", response_model=List[ItemResponse])
def read_items_by_user(user_id: int, db: Session = Depends(get_db)):
    return get_items_by_user(db, user_id)
