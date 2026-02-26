from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from App.db.base import Base
import uuid
from datetime import datetime

class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    video_url = Column(String, nullable=False)
    transcript = Column(String, nullable=True)

    owner = relationship("User", back_populates="videos")
    chunks = relationship(
        "VideoChunk",  
        back_populates="video",
        cascade="all, delete-orphan"
    )