from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    owner_id: UUID  # Fixed: was int, should be UUID to match User model


class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    owner_id: UUID  # Fixed: was int, should be UUID to match User model

    class Config:
        from_attributes = True
