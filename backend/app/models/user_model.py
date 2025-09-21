
from pydantic import BaseModel, EmailStr
from datetime import datetime

class RegisterForm(BaseModel):
    username: str
    email: EmailStr
    JD: datetime
    psw: str
    sub: bool

class LoginForm(BaseModel):
    username: str
    psw: str
    
