# app/routers/admin.py

from fastapi import APIRouter
from typing import Any, Dict, List
from app.core.db import db
from app.models.event_model import Event, EventReq

router = APIRouter()

@router.post(path="/events/get-events", response_model=list)
def get_events(req: EventReq):
    events = []

    docs = db.collection("events").stream()
    for doc in docs:
        obj = doc.to_dict()
        events.append(Event(id=obj.id, dateTime=obj.datetime, imgSrc=obj.imgurl, imgAlt=obj.imgalt, title=obj.title, details=obj.details))

    return events