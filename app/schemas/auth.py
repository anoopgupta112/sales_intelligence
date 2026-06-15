from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserRegister(UserBase):
    password: str
    role: Optional[str] = "representative"  # admin, manager, representative

class UserLogin(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
