# app/routers/user.py

from fastapi import APIRouter, HTTPException
from app.core.utils import User
from app.models.user_model import UserChanges, UserData
from app.core.mc import get_mc_player_info_as_user

router = APIRouter()

@router.post(path="/user/update", response_model=dict)
def update_userdata(incoming_changes: UserChanges):
    user = User()
    user.fromUUID(incoming_changes.id)
    userdata : UserData = user.fetch_userdata()
    userdata_dict = userdata.dict()
    changes = incoming_changes.dict(exclude_unset=True)
    for field in changes:
        userdata_dict[field] = changes.get(field)

    userdata = UserData(**userdata_dict)

    update_result = user.update_userdata(userdata)
    if update_result:
        return {"status": "success"}

@router.post(path="/user/fetch", response_model=dict)
async def fetch_userdata(user_id: str):
    response = {}
    user = User()
    user.fromUUID(user_id)
    response["userdata"] = user.fetch_userdata().dict()
    response["mc"] = (await get_mc_player_info_as_user(user_id))["player_info"]
    return response
