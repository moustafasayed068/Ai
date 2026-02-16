from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from App.schemas.chat import ChatCreate, ChatResponse, ChatRequest, MessageResponse
from App.repositories.chat import create_chat, get_chat, create_message, get_messages, delete_chat
from App.db.session import get_db
from App.services.llm import LLMService
from App.core.dependencies import get_current_user
from App.schemas import UserResponse

router = APIRouter(prefix="/llm/chat", tags=["Chat"])

def get_llm_service():
    return LLMService()


@router.post("/", response_model=List[MessageResponse])
def send_or_create_chat(
    request: ChatRequest,
    title: str,
    chat_id: UUID | None = None,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service)
):
    
    chat = create_chat(db, title=title, owner_id=current_user.id, chat_id=chat_id)

    
    create_message(db, chat.id, request.message, "user")

    
    history = [{"role": m.role, "content": m.content} for m in get_messages(db, chat.id)]

    
    ai_reply = llm.chat(history)

    
    create_message(db, chat.id, ai_reply, "assistant")

    
    return get_messages(db, chat.id)


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
def get_all_messages(
    chat_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot view this chat")
    
    return get_messages(db, chat_id)

@router.delete("/{chat_id}", status_code=204)
def delete_chat_endpoint(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    deleted = delete_chat(db, chat_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=403, detail="You cannot delete this chat or it does not exist")
    return
