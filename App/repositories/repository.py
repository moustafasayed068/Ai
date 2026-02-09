from sqlalchemy.orm import Session
from ..models import User, Item
from ..schemas import UserCreate, ItemCreate
from ..core.auth import get_password_hash

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(name=user.name, age=user.age, email=user.email, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def update_user(db: Session, user_id: int, user: UserCreate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    db_user.name = user.name
    db_user.age = user.age
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    db.delete(db_user)
    db.commit()
    return True


def create_item(db: Session, item: ItemCreate):
    db_item = Item(title=item.title, description=item.description, owner_id=item.owner_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item(db: Session, item_id: int):
    return db.query(Item).filter(Item.id == item_id).first()


def get_items_by_user(db: Session, user_id: int):
    return db.query(Item).filter(Item.owner_id == user_id).all()
