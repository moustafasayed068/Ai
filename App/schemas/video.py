from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from datetime import datetime
 
class VideoResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    video_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: UUID
    video_id: UUID
    chunk_index: int
    summary: Optional[str]
    start_time: Optional[float]
    end_time: Optional[float]

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    chunk_id: UUID
    video_id: UUID
    title: str
    summary: Optional[str]
    similarity_score: float
    start_time: Optional[float]
    end_time: Optional[float]



class VideoChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    content: str
    summary: Optional[str]
    start_time: Optional[float]
    end_time: Optional[float]

    class Config:
        from_attributes = True


class VideoWithChunksResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None  # optional: main transcript or first chunk summary
    video_url: str
    created_at: datetime
    chunks: List[VideoChunkResponse] = []

    class Config:
        from_attributes = True