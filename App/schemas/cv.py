from pydantic import BaseModel
from typing import Optional
import uuid


# ---------- Upload ----------

class CVUploadResponse(BaseModel):
    id: uuid.UUID
    name: Optional[str]
    education: Optional[str]
    experience_years: Optional[float]
    summary: Optional[str]
    topics: list[str]
    file_url: str

    class Config:
        from_attributes = True


# ---------- Single CV ----------

class CVSkillOut(BaseModel):
    id: uuid.UUID
    skill: str
    category: str

    class Config:
        from_attributes = True


class CVOut(BaseModel):
    id: uuid.UUID
    owner_id: Optional[uuid.UUID]
    name: Optional[str]
    education: Optional[str]
    experience_years: Optional[float]
    summary: Optional[str]
    file_url: str
    skills: list[CVSkillOut] = []

    class Config:
        from_attributes = True


# ---------- Match ----------

class MatchRequest(BaseModel):
    description: str                        # plain text e.g. "senior Python backend with AI experience"
    must_have: Optional[list[str]] = []     # hard skill filter e.g. ["Python", "FastAPI"]
    top_k: int = 5


class MatchedCV(BaseModel):
    cv_id: uuid.UUID
    name: Optional[str]
    education: Optional[str]
    experience_years: Optional[float]
    summary: Optional[str]
    file_url: str
    matched_skills: list[str]               # which skills matched
    match_score: float                      # lower = better (L2 distance)
