
from pydantic import BaseModel, EmailStr

class RegisterForm(BaseModel):
    username: str
    email: EmailStr
    psw: str
    sub: bool

class LoginForm(BaseModel):
    email: EmailStr
    psw: str
    
