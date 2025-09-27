# app/models/admin_models.py

from pydantic import BaseModel, EmailStr
from datetime import datetime

class AdminData(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: str = 'admin'
    rank: str
    logTime: datetime
    isActive: bool = False
    probation: bool = False

class AdminRegisterForm(BaseModel):
    username: str
    email: EmailStr
    psw: str
    role: str
    rank: str
    admin_code: int

class AdminLoginForm(BaseModel):
    email: EmailStr
    psw: str
    
