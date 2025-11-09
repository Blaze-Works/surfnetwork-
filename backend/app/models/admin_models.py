# app/models/admin_models.py

from pydantic import BaseModel, EmailStr
from typing import List
from datetime import datetime

class AdminData(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: str = 'admin'
    badges: List[str]
    color: str = "#21b4b4"
    logTime: datetime
    isActive: bool = False
    probation: bool = False

class AdminMessageSubmission(BaseModel):
    admin_id: str
    message: str
    time: datetime

class AdminRegisterForm(BaseModel):
    username: str
    email: EmailStr
    psw: str
    admin_code: int

class AdminLoginForm(BaseModel):
    email: EmailStr
    psw: str
    
