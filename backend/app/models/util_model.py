# app/models/util_model.py

from pydantic import BaseModel, EmailStr
from fastapi import Query
from typing import Optional, List
from datetime import datetime

class UserData(BaseModel):
    id: str
    username: str
    email: EmailStr
    JD: datetime
    confirm_email: bool = False
    player_id: Optional[str] = ""
    