from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from App.schemas.chat import ChatCreate, ChatResponse, MessageCreate, MessageResponse
from App.repositories.chat import create_chat, get_chat, create_message, get_messages, delete_chat
from App.db.session import get_db
from App.services.llm import LLMService
from App.core.dependencies import get_current_user
from App.schemas import UserResponse

router = APIRouter(prefix="/chat", tags=["Chat"])

def get_llm_service():
    return LLMService()


# --- Chat endpoints --- #

@router.post("/", response_model=ChatResponse)
def create_chat_endpoint(
    chat: ChatCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_chat(db, chat, current_user.id)


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    chat_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot view this chat")
    return get_messages(db, chat_id)


@router.post("/{chat_id}/message", response_model=List[MessageResponse])
def send_message(
    chat_id: int,
    request: MessageCreate,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
    current_user: UserResponse = Depends(get_current_user)
):
    chat = get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot send messages to this chat")

    # 1️⃣ Save user message
    create_message(db, chat_id, request.content)

    # 2️⃣ Prepare history
    history = [{"role": "user", "content": m.content} for m in get_messages(db, chat_id)]

    # 3️⃣ Get AI reply
    ai_reply = llm.chat(history)

    # 4️⃣ Save AI message
    create_message(db, chat_id, ai_reply)

    # 5️⃣ Return all messages
    return get_messages(db, chat_id)


@router.delete("/{chat_id}", status_code=204)
def delete_chat_endpoint(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    deleted = delete_chat(db, chat_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=403, detail="You cannot delete this chat or it does not exist")
    return
