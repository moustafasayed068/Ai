from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from App.schemas.chat import MessageResponse
from App.repositories.chat import create_chat, get_chat, create_message, get_messages, delete_chat
from App.db.session import get_db
from App.services.llm import LLMService
from App.core.dependencies import get_current_user
from App.schemas.user import UserResponse
from App.schemas.chat import ChatWithFileResponse
from App.client.supabase import SupabaseStorage

router = APIRouter(prefix="/llm/chat", tags=["Chat"])


async def get_llm_service():
    return LLMService()


async def get_storage():
    return SupabaseStorage()


@router.post("/", response_model=ChatWithFileResponse)
async def send_or_create_chat(
    message: str = Form(...),
    title: str = Form(...),
    chat_id: UUID | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
    storage: SupabaseStorage = Depends(get_storage)
):
    file_url = None
    file_text_preview = None

    if file:
        file_bytes = await file.read()
        from fastapi.concurrency import run_in_threadpool
        file_url = await run_in_threadpool(
            storage.upload_file, file_bytes, file.filename, current_user.id
        )

        try:
            file_text_preview = file_bytes.decode("utf-8")[:1000]
        except UnicodeDecodeError:
            file_text_preview = f"[File uploaded: {file.filename}]"

    chat = await create_chat(db, title=title, owner_id=current_user.id, chat_id=chat_id)

    user_msg = message
    if file_text_preview:
        user_msg += f"\n[File content preview: {file_text_preview}]"
    await create_message(db, chat.id, user_msg, "user")

    history = [{"role": m.role, "content": m.content} for m in await get_messages(db, chat.id)]

    try:
        ai_reply = await llm.chat(history, file_url=file_url)
        await create_message(db, chat.id, ai_reply, "assistant")
    except Exception:
        ai_reply = "[LLM failed to generate a reply]"
        await create_message(db, chat.id, ai_reply, "assistant")

    return ChatWithFileResponse(
        messages=await get_messages(db, chat.id),
        file_url=file_url
    )


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def get_all_messages(
    chat_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat = await get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot view this chat")
    return await get_messages(db, chat_id)


@router.delete("/{chat_id}", status_code=204)
async def delete_chat_endpoint(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    deleted = await delete_chat(db, chat_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=403, detail="You cannot delete this chat or it does not exist")