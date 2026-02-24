from sqlalchemy.orm import Session
from App.models.video import Video
from App.models.chat import Chat
import uuid
from App.client.supabase import SupabaseStorage
from typing import Optional
import numpy as np

async def create_video(db: Session, title: str, description: str, owner_id: str, video_url: str) -> Video:
    video = Video(
        id=uuid.uuid4(),
        title=title,
        description=description,
        owner_id=owner_id,
        video_url=video_url
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


async def update_video_transcript(db: Session, video_id, transcript: str) -> Video:
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise ValueError("Video not found")
    video.transcript = transcript
    db.commit()
    db.refresh(video)
    return video


async def save_video_embedding(db: Session, video_id, vector: list[float]) -> Video:
    """Save the embedding vector directly on the Video row (videos.embedding column)."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise ValueError(f"Video {video_id} not found when saving embedding")
    video.embedding = vector
    db.commit()
    db.refresh(video)
    return video


async def get_chat_by_video(db: Session, video_id) -> Chat | None:
    """Return the Chat whose id matches the video_id (if one was created)."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        return None
    return db.query(Chat).filter(Chat.id == video.id).first()


async def get_videos_with_embeddings(db: Session) -> list[Video]:
    """Return all videos that have an embedding stored in their embedding column."""
    return db.query(Video).filter(Video.embedding.isnot(None)).all()

def to_float_list(array_like) -> list[float]:
    """Convert numpy array or list to Python list of floats."""
    if hasattr(array_like, "tolist"):
        array_like = array_like.tolist()
    return [float(x) for x in array_like]


async def get_storage():
    return SupabaseStorage()


def _extract_public_url(storage_response) -> Optional[str]:
    if not storage_response:
        return None
    if isinstance(storage_response, str):
        return storage_response
    for key in ("publicUrl", "public_url", "publicURL", "url"):
        if isinstance(storage_response, dict) and key in storage_response:
            return storage_response[key]
    return str(storage_response)


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(v1, dtype=float)
    b = np.array(v2, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
