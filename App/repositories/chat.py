from sqlalchemy.orm import Session
from typing import Optional, List
from App.models.chat import Chat, Message
from uuid import UUID
import uuid

def create_chat(db: Session, title: str, owner_id: int, chat_id: UUID | None = None) -> Chat:
    if chat_id:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if chat:
            return chat
    
    db_chat = Chat(id=chat_id or uuid.uuid4(), title=title, owner_id=owner_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def get_chat(db: Session, chat_id: UUID) -> Optional[Chat]:
    return db.query(Chat).filter(Chat.id == chat_id).first()

def get_chats_by_user(db: Session, owner_id: int) -> List[Chat]:
    return db.query(Chat).filter(Chat.owner_id == owner_id).all()

def delete_chat(db: Session, chat_id: UUID, user_id: int) -> bool:
    chat = get_chat(db, chat_id)
    if not chat or chat.owner_id != user_id:
        return False
    db.delete(chat)
    db.commit()
    return True

def create_message(db: Session, chat_id: UUID, content: str, role: str) -> Message:
    msg = Message(chat_id=chat_id, content=content, role=role)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_messages(db: Session, chat_id: UUID) -> List[Message]:
    return db.query(Message).filter(Message.chat_id == chat_id).all()