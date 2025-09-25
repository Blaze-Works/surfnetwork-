# app/routers/login.py

from fastapi import APIRouter
from app.models.util_model import UserData
from app.models.user_model import LoginForm
from app.core.utils import User, discord_login, discord_callback

router = APIRouter()

@router.post(path="/login/ppsecure", response_model=dict)
def user_login(form: LoginForm):
    user = User()
    return user.from_login(form)

@router.get(path="/login/auth/discord")
def discord_auth():
    return discord_login()

@router.post(path="/login/auth/discord/callback")
def discord_auth_callback(code):
    return discord_callback(code)

@router.post(path="/login/req-psw-reset", response_model=dict)
def request_password_reset(user_id: str):
    user = User()
    user.fromUUID(user_id)
    return user.request_password_reset()

@router.post(path="/login/validate-psw-reset", response_model=dict)
def validate_password_reset(user_id: str, reset_code: int):
    user = User()
    user.fromUUID(user_id)
    return user.validate_password_request(reset_code)

@router.post(path="/login/forget-psw", response_model=dict)
def change_password(change_key: str, user_id: str, new_password: str):
    user = User()
    user.fromUUID(user_id)
    return user.update_psw(change_key, new_password)

@router.post(path="/login/fetch-userdata", response_model=UserData)
def fetch_userdata(user_id: str):
    user = User()
    user.fromUUID(user_id)
    return user.fetch_userdata()