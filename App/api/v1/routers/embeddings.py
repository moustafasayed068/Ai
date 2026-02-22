from fastapi import APIRouter, HTTPException
from App.models.embeddings import EmbRequest, EmbResponse
from App.services.llm import LLMService

router = APIRouter()
llm_service = LLMService()



@router.post("/embed", response_model=EmbResponse)
async def get_embeddings(request: EmbRequest):
    try:
        embeddings = llm_service.emb(request.texts)
        return {"embeddings": embeddings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")