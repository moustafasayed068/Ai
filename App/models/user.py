from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from App.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    items = relationship("Item", back_populates="owner", cascade="all, delete")
    chats = relationship("Chat", back_populates="owner", cascade="all, delete")
