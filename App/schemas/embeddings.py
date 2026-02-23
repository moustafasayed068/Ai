from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class EmbRequest(BaseModel):
    texts: List[str]
    chat_id: Optional[UUID] = None


class EmbResponse(BaseModel):
    embeddings: List[float]
    chat_id: str