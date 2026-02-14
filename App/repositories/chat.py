from sqlalchemy.orm import Session
from typing import Optional, List
from App.models import Chat, Message
from ..schemas.chat import ChatCreate
import logging

logger = logging.getLogger(__name__)

# --- CHAT --- #

def create_chat(db: Session, chat: ChatCreate, owner_id: int) -> Chat:
    """Create a new chat"""
    db_chat = Chat(title=chat.title, owner_id=owner_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def get_chat(db: Session, chat_id: int) -> Optional[Chat]:
    return db.query(Chat).filter(Chat.id == chat_id).first()

def get_chats_by_user(db: Session, owner_id: int) -> List[Chat]:
    return db.query(Chat).filter(Chat.owner_id == owner_id).all()

def delete_chat(db: Session, chat_id: int, user_id: int) -> bool:
    """Delete chat only if it belongs to the user"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        return False
    if chat.owner_id != user_id:
        return False
    db.delete(chat)
    db.commit()
    return True

# --- MESSAGE --- #

def create_message(db: Session, chat_id: int, content: str) -> Message:
    msg = Message(chat_id=chat_id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_messages(db: Session, chat_id: int) -> List[Message]:
    return db.query(Message).filter(Message.chat_id == chat_id).all()
