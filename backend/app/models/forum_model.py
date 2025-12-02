# app/models/forum_model.py

from pydantic import BaseModel, EmailStr
from fastapi import Query
from typing import Optional, List
from datetime import datetime

class ForumSubmission(BaseModel):
    user_id: str
    category: str
    title: str
    content: str

class ForumReplySubmission(BaseModel):
    user_id: str
    parent_id: str
    category: str
    content: str

class ForumMessage(BaseModel):
    id: str
    parent_id: str
    author: str
    content: str
    time: str
    likes: int = 0
    dislikes: int = 0
    replies: list

class Forum(BaseModel):
    id: str
    topic: str
    author: str
    content: str
    time: str
    likes: int = 0
    dislikes: int = 0
    replies: list
