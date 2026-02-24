from sqlalchemy import Column, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
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
    view_duration = Column(Float, default=0.0)
    video_url = Column(String, nullable=False)
    transcript = Column(String, nullable=True)
    embedding = Column(Vector(1536), nullable=True)  

    owner = relationship("User", back_populates="videos")