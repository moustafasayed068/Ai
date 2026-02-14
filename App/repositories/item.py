from sqlalchemy.orm import Session
from typing import Optional
from App.models import Item
from ..schemas import ItemCreate
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

# --- READ --- #

def get_item(db: Session, item_id: int) -> Optional[Item]:
    return db.query(Item).filter(Item.id == item_id).first()

def get_items_by_user(db: Session, user_id: int) -> list[Item]:
    return db.query(Item).filter(Item.owner_id == user_id).all()


# --- CREATE --- #

def create_item(
    local_db: Session,
    supabase_db: Optional[Session],
    item: ItemCreate
) -> Item:
    """Create item with SAME ID in both databases if needed"""
    # Create in local DB first if needed
    local_item = None
    if settings.DB_MODE in ("local", "both"):
        local_item = Item(
            title=item.title,
            description=item.description,
            owner_id=item.owner_id
        )
        local_db.add(local_item)
        local_db.commit()
        local_db.refresh(local_item)

    # Create in Supabase if needed
    if settings.DB_MODE in ("supabase", "both") and supabase_db:
        try:
            supabase_item = Item(
                id=local_item.id if local_item else None,  # sync ID if local exists
                title=item.title,
                description=item.description,
                owner_id=item.owner_id
            )
            supabase_db.add(supabase_item)
            supabase_db.commit()
        except Exception as e:
            logger.error(f"Supabase create failed: {e}")
            if settings.SUPABASE_FAILURE_STRATEGY == "fail" and local_item:
                local_db.rollback()
                raise

    return local_item if local_item else supabase_item


# --- UPDATE --- #

def update_item(
    local_db: Session,
    supabase_db: Optional[Session],
    item_id: int,
    item: ItemCreate
) -> Optional[Item]:
    updated_item = None

    dbs = []
    if settings.DB_MODE in ("local", "both"):
        dbs.append(local_db)
    if settings.DB_MODE in ("supabase", "both"):
        dbs.append(supabase_db)

    for db in dbs:
        if not db:
            continue
        try:
            db_item = db.query(Item).filter(Item.id == item_id).first()
            if db_item:
                db_item.title = item.title
                db_item.description = item.description
                db_item.owner_id = item.owner_id
                db.commit()
                db.refresh(db_item)
                if not updated_item:
                    updated_item = db_item
        except Exception as e:
            logger.error(f"Update failed on {db}: {e}")

    return updated_item


# --- DELETE --- #

def delete_item(
    local_db: Session,
    supabase_db: Optional[Session],
    item_id: int
) -> bool:
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
            db_item = db.query(Item).filter(Item.id == item_id).first()
            if db_item:
                db.delete(db_item)
                db.commit()
                success = True
        except Exception as e:
            logger.error(f"Delete failed on {db}: {e}")

    return success
