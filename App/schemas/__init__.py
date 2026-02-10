from pydantic import BaseModel, Field
from typing import Optional


class UserCreate(BaseModel):
    name: str = Field(default="ahmed", description="The name will be inserted in the database")
    age: int
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: str

    class Config:
        from_attributes = True


class Login(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class TokenRequest(BaseModel):
    access_token: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRequest(BaseModel):
    access_token: str


class TokenData(BaseModel):
    email: str | None = None


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
        from_attributes = True
