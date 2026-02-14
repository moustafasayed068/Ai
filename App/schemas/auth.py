from pydantic import BaseModel

class Login(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
