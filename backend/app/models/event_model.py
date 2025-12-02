# app/models/event_models.py

from pydantic import BaseModel, EmailStr
from typing import List
from datetime import datetime

class Event(BaseModel):
    id: str
    dateTime: datetime
    imgSrc: str
    imgAlt: str
    title: str
    details: str

class EventReq(BaseModel):
    order: str
    count: int