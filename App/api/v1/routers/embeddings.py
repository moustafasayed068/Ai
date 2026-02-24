from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID
import uuid
from App.schemas.embeddings import EmbRequest, EmbResponse
from App.services.llm import LLMService
from App.db.session import get_db
from App.repositories.chat import create_chat
from App.repositories.embedding import create_embedding, get_embedding, get_all_embeddings
from App.core.dependencies import get_current_user
from App.models.user import User
import numpy as np

router = APIRouter()
llm_service = LLMService()


def to_float_list(array_like):
    """Convert numpy array or list to Python list of floats"""
    if hasattr(array_like, "tolist"):
        array_like = array_like.tolist()
    return [float(x) for x in array_like]


@router.post("/embed", response_model=EmbResponse)
async def create_embedding_endpoint(
    request: EmbRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        chat_id = request.chat_id or str(uuid.uuid4())

        create_chat(
            db,
            title="Embedding Chat",
            owner_id=current_user.id,
            chat_id=chat_id
        )

        embeddings = llm_service.emb(request.texts)
        if not embeddings or not isinstance(embeddings, list):
            raise HTTPException(status_code=500, detail="Embedding service returned invalid result")

        vector = embeddings[0]
        vector = vector.tolist() if hasattr(vector, "tolist") else vector

        emb_obj = create_embedding(db, chat_id=chat_id, vector=vector)

        return {
            "embeddings": to_float_list(emb_obj.vector),
            "chat_id": chat_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {e}")


@router.post("/similarity", response_model=dict)
async def similarity_search(
    text: str,
    db: Session = Depends(get_db),
):
    """
    Compare similarity using Cosine, Euclidean, Dot Product, and Hybrid score.
    Returns top 5 similar embeddings for each algorithm.
    """
    try:
        query_vector = llm_service.emb([text])[0]
        query_vector = query_vector.tolist() if hasattr(query_vector, "tolist") else query_vector

        all_embeddings = get_all_embeddings(db)
        if not all_embeddings:
            raise HTTPException(status_code=404, detail="No embeddings in database")

        
        def cosine_sim(v1, v2):
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

        def euclidean_dist(v1, v2):
            return np.linalg.norm(np.array(v1) - np.array(v2))

        def dot_product(v1, v2):
            return np.dot(v1, v2)

        def hybrid_score(v1, v2, alpha=0.5):
            """
            Combines normalized cosine similarity and inverse Euclidean distance
            alpha = weight for cosine, (1-alpha) weight for Euclidean
            """
            cos = cosine_sim(v1, v2)
            euclid = euclidean_dist(v1, v2)
            inv_euclid = 1 / (1 + euclid)  
            return alpha * cos + (1 - alpha) * inv_euclid

        cosine_results = sorted(all_embeddings, key=lambda e: -cosine_sim(query_vector, e.vector))[:5]
        euclidean_results = sorted(all_embeddings, key=lambda e: euclidean_dist(query_vector, e.vector))[:5]
        dot_results = sorted(all_embeddings, key=lambda e: -dot_product(query_vector, e.vector))[:5]
        hybrid_results = sorted(all_embeddings, key=lambda e: -hybrid_score(query_vector, e.vector))[:5]

        
        return {
            "cosine_top5": [{"chat_id": str(e.chat_id)} for e in cosine_results],
            "euclidean_top5": [{"chat_id": str(e.chat_id)} for e in euclidean_results],
            "dot_top5": [{"chat_id": str(e.chat_id)} for e in dot_results],
            "hybrid_top5": [{"chat_id": str(e.chat_id)} for e in hybrid_results],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity search error: {e}")

@router.get("/embed", response_model=EmbResponse)
async def get_embedding_endpoint(chat_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve embedding vector by chat_id
    """
    emb = get_embedding(db, chat_id=chat_id)
    if not emb:
        raise HTTPException(status_code=404, detail="Embedding not found for provided chat_id")
    return {
        "embeddings": to_float_list(emb.vector),
        "chat_id": str(chat_id)
    }