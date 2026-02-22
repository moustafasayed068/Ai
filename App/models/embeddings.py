from pydantic import BaseModel
from typing import List

class EmbRequest(BaseModel):
    texts: List[str]

class EmbResponse(BaseModel):
    embeddings: List[List[float]]