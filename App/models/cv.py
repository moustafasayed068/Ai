import uuid
from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from App.db.base import Base


class CV(Base):
    __tablename__ = "cvs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    file_url = Column(Text, nullable=False)
    full_text = Column(Text, nullable=True)
    name = Column(String(255), nullable=True)
    education = Column(Text, nullable=True)       # e.g. "BSc CS, Cairo University 2020"
    experience_years = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)         # LLM summary of full CV
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    skills = relationship("CVSkill", back_populates="cv", cascade="all, delete-orphan")


class CVSkill(Base):
    __tablename__ = "cv_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_id = Column(UUID(as_uuid=True), ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)

    # The skill/topic text  e.g. "Python", "Machine Learning", "3 years experience"
    skill = Column(String(500), nullable=False)

    # Category helps distinguish during search and display
    # values: "topic" | "education" | "experience"
    category = Column(String(50), nullable=False, default="topic")

    embedding = Column(Vector, nullable=True)

    cv = relationship("CV", back_populates="skills")
