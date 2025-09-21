# app/models/util_model.py

from pydantic import BaseModel, EmailStr
from fastapi import Query
from typing import Optional, List
from datetime import datetime

class UserData(BaseModel):
    id: str
    firstname: str
    lastname: str
    email: EmailStr
    phone: str
    age: int
    DOB: datetime
    profile_picture_url: str
    confirm_email: bool = False