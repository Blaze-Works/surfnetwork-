# app/routers/user.py

from fastapi import APIRouter, HTTPException
from app.core.utils import User
from app.models.user_model import UserChanges, UserData

router = APIRouter()

@router.post(path="/user/update", response_model=dict)
def update_userdata(incoming_changes: UserChanges):
    user = User()
    user.fromUUID(incoming_changes.id)
    userdata : UserData = user.fetch_userdata()
    for field in incoming_changes:
        userdata[field] = incoming_changes[field]

    print(userdata)
    return {}