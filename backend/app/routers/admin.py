# app/routers/admin.py

from fastapi import APIRouter
from app.models.admin_models import AdminLoginForm, AdminRegisterForm
from app.core.util import Admin

router = APIRouter()

@router.post(path="/admin/login/ppsecure", response_model=dict)
def admin_login(form: AdminLoginForm):
    admin = Admin()
    return admin.from_login(form)

def admin_register(form: AdminRegisterForm):
    admin = Admin()
    return admin.from_register(form)
