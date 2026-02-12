from sqlalchemy.orm import Session
from typing import Optional
from App.models import User, Item
from ..schemas import UserCreate, ItemCreate
from ..core.auth import get_password_hash
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

# ==================== USER OPERATIONS ====================

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID - reads from primary DB only"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email - reads from primary DB only"""
    return db.query(User).filter(User.email == email).first()

def create_user(
    local_db: Session, 
    supabase_db: Optional[Session], 
    user: UserCreate
) -> User:
    """Create user with SAME ID in both databases"""
    hashed_password = get_password_hash(user.password)
    
    if settings.DB_MODE == "local":
        # Local only
        db_user = User(name=user.name, age=user.age, email=user.email, hashed_password=hashed_password)
        local_db.add(db_user)
        local_db.commit()
        local_db.refresh(db_user)
        return db_user
    
    elif settings.DB_MODE == "supabase":
        # Supabase only
        db_user = User(name=user.name, age=user.age, email=user.email, hashed_password=hashed_password)
        supabase_db.add(db_user)
        supabase_db.commit()
        supabase_db.refresh(db_user)
        return db_user
    
    elif settings.DB_MODE == "both":
        # Create in local first to get ID
        local_user = User(name=user.name, age=user.age, email=user.email, hashed_password=hashed_password)
        local_db.add(local_user)
        local_db.commit()
        local_db.refresh(local_user)
        
        try:
            # Create in Supabase with SAME ID
            supabase_user = User(
                id=local_user.id,  # Use same ID!
                name=user.name,
                age=user.age,
                email=user.email,
                hashed_password=hashed_password
            )
            supabase_db.add(supabase_user)
            supabase_db.commit()
            logger.info(f"User {local_user.id} synced to both databases")
        except Exception as e:
            logger.error(f"Supabase sync failed: {e}")
            if settings.SUPABASE_FAILURE_STRATEGY == "fail":
                local_db.rollback()
                raise
            # Continue with local only
        
        return local_user

def update_user(
    local_db: Session,
    supabase_db: Optional[Session],
    user_id: int,
    user: UserCreate
) -> Optional[User]:
    """Update user in both databases"""
    if settings.DB_MODE == "local":
        db_user = local_db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        db_user.name = user.name
        db_user.age = user.age
        db_user.email = user.email
        local_db.commit()
        local_db.refresh(db_user)
        return db_user
    
    elif settings.DB_MODE == "supabase":
        db_user = supabase_db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        db_user.name = user.name
        db_user.age = user.age
        db_user.email = user.email
        supabase_db.commit()
        supabase_db.refresh(db_user)
        return db_user
    
    elif settings.DB_MODE == "both":
        # Update local
        db_user = local_db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        db_user.name = user.name
        db_user.age = user.age
        db_user.email = user.email
        local_db.commit()
        local_db.refresh(db_user)
        
        # Update Supabase
        try:
            supabase_user = supabase_db.query(User).filter(User.id == user_id).first()
            if supabase_user:
                supabase_user.name = user.name
                supabase_user.age = user.age
                supabase_user.email = user.email
                supabase_db.commit()
        except Exception as e:
            logger.error(f"Supabase update failed: {e}")
            if settings.SUPABASE_FAILURE_STRATEGY == "fail":
                local_db.rollback()
                raise
        
        return db_user

def delete_user(
    local_db: Session,
    supabase_db: Optional[Session],
    user_id: int
) -> bool:
    """Delete user from both databases"""
    if settings.DB_MODE == "local":
        db_user = local_db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        local_db.delete(db_user)
        local_db.commit()
        return True
    
    elif settings.DB_MODE == "supabase":
        db_user = supabase_db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        supabase_db.delete(db_user)
        supabase_db.commit()
        return True
    
    elif settings.DB_MODE == "both":
        db_user = local_db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        local_db.delete(db_user)
        local_db.commit()
        
        try:
            supabase_user = supabase_db.query(User).filter(User.id == user_id).first()
            if supabase_user:
                supabase_db.delete(supabase_user)
                supabase_db.commit()
        except Exception as e:
            logger.error(f"Supabase delete failed: {e}")
        
        return True

# ==================== ITEM OPERATIONS ====================

def get_item(db: Session, item_id: int) -> Optional[Item]:
    return db.query(Item).filter(Item.id == item_id).first()

def get_items_by_user(db: Session, user_id: int) -> list[Item]:
    return db.query(Item).filter(Item.owner_id == user_id).all()

def create_item(
    local_db: Session,
    supabase_db: Optional[Session],
    item: ItemCreate
) -> Item:
    """Create item with SAME ID in both databases"""
    if settings.DB_MODE == "local":
        db_item = Item(title=item.title, description=item.description, owner_id=item.owner_id)
        local_db.add(db_item)
        local_db.commit()
        local_db.refresh(db_item)
        return db_item
    
    elif settings.DB_MODE == "supabase":
        db_item = Item(title=item.title, description=item.description, owner_id=item.owner_id)
        supabase_db.add(db_item)
        supabase_db.commit()
        supabase_db.refresh(db_item)
        return db_item
    
    elif settings.DB_MODE == "both":
        # Create in local first
        local_item = Item(title=item.title, description=item.description, owner_id=item.owner_id)
        local_db.add(local_item)
        local_db.commit()
        local_db.refresh(local_item)
        
        try:
            # Create in Supabase with SAME ID
            supabase_item = Item(
                id=local_item.id,
                title=item.title,
                description=item.description,
                owner_id=item.owner_id
            )
            supabase_db.add(supabase_item)
            supabase_db.commit()
        except Exception as e:
            logger.error(f"Item Supabase sync failed: {e}")
            if settings.SUPABASE_FAILURE_STRATEGY == "fail":
                local_db.rollback()
                raise
        
        return local_item

def update_item(
    local_db: Session,
    supabase_db: Optional[Session],
    item_id: int,
    item: ItemCreate
) -> Optional[Item]:
    if settings.DB_MODE == "local":
        db_item = local_db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return None
        db_item.title = item.title
        db_item.description = item.description
        db_item.owner_id = item.owner_id
        local_db.commit()
        local_db.refresh(db_item)
        return db_item
    
    elif settings.DB_MODE == "supabase":
        db_item = supabase_db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return None
        db_item.title = item.title
        db_item.description = item.description
        db_item.owner_id = item.owner_id
        supabase_db.commit()
        supabase_db.refresh(db_item)
        return db_item
    
    elif settings.DB_MODE == "both":
        db_item = local_db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return None
        db_item.title = item.title
        db_item.description = item.description
        db_item.owner_id = item.owner_id
        local_db.commit()
        local_db.refresh(db_item)
        
        try:
            supabase_item = supabase_db.query(Item).filter(Item.id == item_id).first()
            if supabase_item:
                supabase_item.title = item.title
                supabase_item.description = item.description
                supabase_item.owner_id = item.owner_id
                supabase_db.commit()
        except Exception as e:
            logger.error(f"Item Supabase update failed: {e}")
        
        return db_item

def delete_item(
    local_db: Session,
    supabase_db: Optional[Session],
    item_id: int
) -> bool:
    if settings.DB_MODE == "local":
        db_item = local_db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return False
        local_db.delete(db_item)
        local_db.commit()
        return True
    
    elif settings.DB_MODE == "supabase":
        db_item = supabase_db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return False
        supabase_db.delete(db_item)
        supabase_db.commit()
        return True
    
    elif settings.DB_MODE == "both":
        db_item = local_db.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            return False
        local_db.delete(db_item)
        local_db.commit()
        
        try:
            supabase_item = supabase_db.query(Item).filter(Item.id == item_id).first()
            if supabase_item:
                supabase_db.delete(supabase_item)
                supabase_db.commit()
        except Exception as e:
            logger.error(f"Item Supabase delete failed: {e}")
        
        return True