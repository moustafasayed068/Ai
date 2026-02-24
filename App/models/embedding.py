from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from App.db.base import Base

class Embedding(Base):
    __tablename__ = "embeddings"
    
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), primary_key=True)
    vector = Column(Vector(1536))  
    
    chat = relationship("Chat", back_populates="embedding")