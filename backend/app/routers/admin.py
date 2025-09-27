# app/routers/admin.py

from fastapi import APIRouter
from app.models.admin_models import AdminLoginForm, AdminRegisterForm
from app.core.utils import Admin, set_admin_code
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

# Note: The admin registration endpoint is protected by an admin code for security.
# Ensure to provide the correct admin code in registration requests.

def reset_admin_code_periodically():
    admin_code = int(''.join(random.choices('0123456789', k=8)))
    set_admin_code(admin_code)
    threading.Timer(300, reset_admin_code_periodically).start()
    
threading.Timer(300, reset_admin_code_periodically).start()
