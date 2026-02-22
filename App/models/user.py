from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from App.db.base import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    items = relationship("Item", back_populates="owner", cascade="all, delete")
    chats = relationship("Chat", back_populates="owner", cascade="all, delete")
