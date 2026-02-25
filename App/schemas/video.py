from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class VideoResponse(BaseModel):
    video_id: UUID        
    title: str
    description: str
    transcript: Optional[str]
    video_url: str

    class Config:
        from_attributes = True


class VideoSearchResult(BaseModel):
    video_id: UUID
    title: str
    description: str
    video_url: str
    transcript: Optional[str]
    similarity_score: float

    class Config:
        from_attributes = True