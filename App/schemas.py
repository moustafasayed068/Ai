from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    age: int

class UserResponse(UserCreate):
    id: int

    class Config:
        orm_mode = True  # مهم جداً عشان Pydantic يتعامل مع كائنات SQLAlchemy
