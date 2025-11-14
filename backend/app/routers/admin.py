# app/routers/admin.py

from fastapi import APIRouter
from typing import Any, Dict, List
from app.core.db import db
from app.models.admin_models import AdminLoginForm, AdminRegisterForm, AdminMessageSubmission
from app.core.utils import Admin, verify_admin, get_admin_code, set_admin_code, time_elasped_string, image_to_dataurl, load_image_from_path
import threading
import random

router = APIRouter()

@router.post(path="/admin/login/ppsecure", response_model=dict)
def admin_login(form: AdminLoginForm):
    admin = Admin()
    return admin.from_login(form)

@router.post(path="/admin/register/ppsecure", response_model=dict)
def admin_register(form: AdminRegisterForm):
    admin = Admin()
    return admin.from_register(form)

@router.get(path="/admin/get-messages", response_model=dict)
def get_admin_message():
    pages = []
    pageCount = 0

    docs = db.collection("admin_messages").stream()
    for doc in docs:
        if verify_admin(doc.id) is True:
            obj = doc.to_dict()
            print(obj)
            admin = Admin()
            admin.fromUUID(doc.id)

            time_str = time_elasped_string(obj.get("time"))

            def badge(titles: List[str]) -> List[Dict[str, str]]:
                badges = []
                for title in titles:
                    badge = {"content": title, "badgeType": "success"}
                    match title:
                        case "owner":
                            badge["badgeType"] = "danger"
                        case "dev":
                            badge["badgeType"] = "danger"
                        case "admin":
                            badge["badgeType"] = "primary"
                        case "moderator":
                            badge["badgeType"] = "primary"

                    badges.append(badge)

                return badges

            print(f"admin_{doc.id}.png")
            
            page = {
                "name": admin.fetch_admindata().username,
                "badges": badge(admin.fetch_admindata().badges),
                "imageSource": image_to_dataurl(load_image_from_path(f"admin_{doc.id}.png")),
                "assentColor": admin.fetch_admindata().color,
                "playerDetail": admin.fetch_admindata().role,
                "messageContent": obj.get("message"),
                "timeDiff": time_str
            }
            pageCount += 1
            pages.append(page)

    return {"page": pages, "pageCount": pageCount}

@router.put(path="/admin/add-message", response_model=dict)
def add_admin_message(admin_message: AdminMessageSubmission):
    if verify_admin(admin_message.admin_id) is True:
        admin = Admin()
        admin.fromUUID(admin_message.admin_id)
        
        message = {
            "message": admin_message.message,
            "time": admin_message.time
        }
        
        try:
            db.collection("admin_messages").document(admin_message.admin_id).set(message)
            return {"message": "Message added successfully"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Invalid admin ID"}

@router.get(path="/admin/get-admin-code")
def get_code(admin_id: str):
    if verify_admin(admin_id) is True:
        code = get_admin_code()
        return {"admin_code": code}

# Note: The admin registration endpoint is protected by an admin code for security.
# Ensure to provide the correct admin code in registration requests.

def reset_admin_code_periodically():
    admin_code = int(''.join(random.choices('0123456789', k=8)))
    set_admin_code(admin_code)
    threading.Timer(300, reset_admin_code_periodically).start()
    
threading.Timer(300, reset_admin_code_periodically).start()
