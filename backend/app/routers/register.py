# app/routers/register.py

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.core.utils import User, file_to_data_url
from app.models.util_model import UserData
from app.models.user_model import RegisterForm
from datetime import datetime

router = APIRouter()

@router.post(path="/register/ppsecure", response_model=UserData)
async def register_user(form: RegisterForm):
    new_user = User()
    status = new_user.from_register(form)
    if status == "success":
        return new_user.fetch_userdata()
    else:
        return JSONResponse(status_code=400, content={"error": str(status)})

@router.post(path="/register/request_confirm_email")
def request_confirm_email(user_id: str):
    user = User()
    user.fromUUID(user_id)
    user.request_confirm_email() 

@router.post(path="/register/confirm_email", response_model=dict)
def confirm_email(user_id: str, email_code: int):
    user = User()
    userdata = user.fromUUID(user_id)
    code = user.fetch_data("email_codes")

    now = datetime.now()
    minutes = now.minute - code["datetime"].minute - (now.second < code["datetime"].second)
    if minutes >= 5:
        return {"status": "Code expired, request another one"}
    
    else:
        if code["digits"] == email_code:
            userdata.confirm_email = True
            return user.from_userdata(userdata, True)

        else:
            return {"error": "Invalid code"}