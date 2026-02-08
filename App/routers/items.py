from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import repository, schemas, database

router = APIRouter()
get_db = database.get_db

@router.post("/", response_model=schemas.ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    # ensure owner exists
    db_user = repository.get_user(db, item.owner_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Owner (user) not found")
    return repository.create_item(db, item)


@router.get("/{item_id}", response_model=schemas.ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = repository.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.get("/user/{user_id}", response_model=List[schemas.ItemResponse])
def read_items_by_user(user_id: int, db: Session = Depends(get_db)):
    return repository.get_items_by_user(db, user_id)
