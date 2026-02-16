from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str

class ChatCreate(BaseModel):
    title: str
    id: UUID | None = None

class ChatResponse(BaseModel):
    id: UUID
    title: str
    owner_id: int
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: UUID
    content: str
    role: str
    chat_id: UUID
    
    class Config:
        from_attributes = True

class ChatWithFileResponse(BaseModel):
    messages: List[MessageResponse]
    file_url: Optional[str] = None
