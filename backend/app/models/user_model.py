# app/models/user_model.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class RegisterForm(BaseModel):
    username: str
    email: EmailStr
    psw: str
    sub: bool

class LoginForm(BaseModel):
    email: EmailStr
    psw: str
    
class UserData(BaseModel):
    id: str
    username: str
    email: EmailStr
    JD: datetime
    confirm_email: bool = False
    bio: Optional[str] = ""
    player_id: Optional[str] = ""

class UserChanges(BaseModel):
    id: str
    username: str
    email: EmailStr
    bio: str