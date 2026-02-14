from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str

    
class ChatCreate(BaseModel):
    title: str


class ChatResponse(BaseModel):
    id: int
    title: str
    owner_id: int

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    content: str
    chat_id: int

    class Config:
        from_attributes = True
