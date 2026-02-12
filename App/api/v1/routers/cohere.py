from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from App.services.cohere import get_chat_response

router = APIRouter(
    prefix="/cohere",
    tags=["Cohere"]
)


class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat_endpoint(request: ChatRequest):
    """Chat with Cohere AI"""
    try:
        reply = get_chat_response(request.message)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))