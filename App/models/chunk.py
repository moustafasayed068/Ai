from sqlalchemy import Column, String, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from App.db.base import Base
import uuid

class VideoChunk(Base):
    __tablename__ = "video_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False)

    chunk_index = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    summary = Column(String, nullable=True)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    embedding = Column(Vector(1536), nullable=False)

    video = relationship("Video", back_populates="chunks")