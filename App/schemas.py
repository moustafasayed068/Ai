from pydantic import BaseModel, Field
from typing import Optional


class UserCreate(BaseModel):
    name: str = Field(default="ahmed", description="The name will be inserted in the database")
    age: int


class UserResponse(UserCreate):
    id: int

    class Config:
        orm_mode = True 


class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    owner_id: int


class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    owner_id: int

    class Config:
        orm_mode = True
