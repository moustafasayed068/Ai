from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    name: str = Field(default="ahmed", description="The name will be inserted in the database")
    age: int


class UserResponse(UserCreate):
    id: int

    class Config:
        orm_mode = True 
