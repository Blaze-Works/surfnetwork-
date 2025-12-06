# app/routers/login.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models.user_model import UserData, LoginForm
from app.core.utils import User, discord_login, discord_callback, get_userid_by_email, send_html_email
from datetime import datetime
import random

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
def request_password_reset(email: str):
    reset_code = random.randint(10000, 99999)
    code_html = f"""<div style='display: flex;height: 61px;width: 249px;justify-content: space-between;align-items: center;flex-direction: row;line-height: 14px;'>{"".join(f"<div style='display: flex;height: 11px;padding: 19px 6px;border: 2px solid #6f67d9;border-radius: 7px;background-color: #f5f5f5;color: #000;font-size: 40px;'>{str(reset_code)[i]}</div>" for i in range(len(str(reset_code))))}</div>"""

    html_content = [
        {
            "type": "table",
            "content": [    
                {
                    "type": "table",
                    "content": [
                        # {"type": "image", "content": "image/logo.png"},
                        {"type": "header", "content": "Reset Your Password"},
                        {"type": "text", "content": "We just need to verify it you before you can reset your password, here's your reset code:"},
                        {"type": "html", "content": code_html},
                        {"type": "html", "content": "This code expires within 5 minutes"},
                        {"type": "text", "content": "Only enter this code on the SurfNetwork website or app. Don't share it with anyone. We'll never ask for it outside any of our platforms."},
                        {"type": "text", "content": "If you see this email and you didn't request a password reset, click below to go to \"Acccount Management\" to secure your account"},
                        {"type": "button", "content": "Account Management", "hyperlink": "#"}
                    ]
                }
            ]
        },
        {
            "type": "table",
            "content": [
                {"type": "text", "content": "This email was sent to you by SurfNetwork because you signed up for a SurfNetwork account.break-linePlease let us know if you feel that this email was sent to you by error."},
                {"type": "text", "content": "© 2025 SurfNetwork"},
                {"type": "list", "content": [
                    {"type": "hyperlink", "content": "Privacy Policy", "link": "#"},
                    {"type": "hyperlink", "content": "Personal Data Protection and Privacy Policy", "link": "#"},
                    {"type": "hyperlink", "content": "Acceptable Use Policy", "link": "#"},
                ]}
            ]
        }
    ]

    send_html_email(to_email=self.email, to_name=self.username, subject="Reset your password - SurfNetwork", html_content=html_content)

    user_reset_request = {
        "datetime": datetime.now(),
        "reset_code": reset_code
    }

    user_id = get_userid_by_email(email)
    try:
        existing_request = db.collection("reset_psw_request").document(user_id)
        if existing_request.get().exists:
            existing_request.delete()

        db.collection("reset_psw_request").document(user_id).set(user_reset_request)
        
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

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