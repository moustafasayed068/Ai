from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(default="ahmed")
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
