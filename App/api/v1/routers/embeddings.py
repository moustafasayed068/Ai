from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from App.schemas.embeddings import EmbRequest, EmbResponse
from App.services.llm import LLMService
from App.db.session import get_db
from App.repositories.chat import create_chat
from App.repositories.embedding import create_embedding, get_embedding

router = APIRouter()
llm_service = LLMService()

@router.post("/embed", response_model=EmbResponse)
async def get_embeddings(request: EmbRequest, owner_id: UUID,db: Session = Depends(get_db)):
    try:
        if request.chat_id:
            chat_id = UUID(request.chat_id)
        else:
            chat = create_chat(db, title="New Chat", owner_id=owner_id)
            chat_id = chat.id

        embeddings = llm_service.emb(request.texts)
        emb_obj = create_embedding(db, chat_id=chat_id, vector=embeddings[0])

        return {
            "embeddings": [float(v) for v in emb_obj.vector],
            "chat_id": str(chat_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")
    
@router.get("/embed", response_model=EmbResponse)
async def get_all(chat_id: UUID, db: Session = Depends(get_db)):
    chat = get_embedding(db , chat_id=chat_id)
    return {
            "embeddings": [float(v) for v in chat.vector],
            "chat_id": str(chat_id)
        }
