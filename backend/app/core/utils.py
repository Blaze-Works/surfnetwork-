# app/core/utils.py

from fastapi import HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from app.core.mail import send_html_email
from app.models.util_model import UserData
from app.models.user_model import RegisterForm, LoginForm
from app.models.admin_models import AdminData, AdminRegisterForm, AdminLoginForm
from app.core.db import db
from datetime import datetime, date, timedelta
from deep_translator import GoogleTranslator
from pathlib import Path
import os
import filetype
import random
import requests
import json
import base64
import bcrypt
import uuid

DISCORD_API_URL= "https://discord.com/api"
CLIENT_ID = os.getenv("CLIENT_KEY")
CLIENT_SECRET_KEY = os.getenv("CLIENT_SECRET_KEY")
REDIRECT_URI = "http://localhost:5729/login/auth/discord/callback"
OAUTH_SCOPE = "identify email"


BADGE_RULES = {

}

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_uuid():
    return str(uuid.uuid4())

def decode_base64_json(data: str) -> dict:
    decoded_bytes = base64.b64decode(data)
    return json.loads(decoded_bytes.decode("utf-8"))

def translate_to_languages(text: str, languages: list[str]) -> dict:
    translations = {}
    for lang in languages:
        try:
            translated = GoogleTranslator(source='auto', target=lang).translate(text)
            translations[lang] = translated
        except Exception as e:
            translations[lang] = f"Error: {str(e)}"
    return translations

def calculate_age(jd):
    today = datetime.now()
    age = today.year - jd.year - ((today.month, today.day) < (jd.month, jd.day))
    return age

def discord_login():

    discord_login_url = (
        f"{DISCORD_API_URL}/oauth2/authorize"
        f"?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
        f"&response_type=code&scope={OAUTH_SCOPE}"
    )

    return RedirectResponse(url=discord_login_url)

def discord_callback(code):
    if code is None:
        raise HTTPException(status_code=400, detail={"error": "No code returned from Discord"})

    # Exchange code for access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET_KEY,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": OAUTH_SCOPE,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token = requests.post(f"{DISCORD_API_URL}/oauth2/token", data=data, headers=headers).json()

    # Get user info
    access_token = token["access_token"]
    user = requests.get(
        f"{DISCORD_API_URL}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    new_user = User()
    return new_user.from_discord_login()

def load_image_from_path(image_path: str) -> bytes:
    import filetype

    p = Path(image_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail={"error": "Image not found"})
    if not p.is_file():
        raise HTTPException(status_code=400, detail={"error": "Invalid image path"})

    try:
        image_bytes = p.read_bytes()
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

    # Validate that the file is an image using filetype
    kind = filetype.guess(image_bytes)
    if kind is None or not kind.mime.startswith('image/'):
        raise HTTPException(status_code=400, detail={"error": "File is not a valid image"})

    return image_bytes

def image_to_dataurl(image) -> str:
    import filetype

    if isinstance(image, (str, Path)):
        with open(image, 'rb') as f:
            image_bytes = f.read()
    else:
        image_bytes = image

    # Detect image type using filetype
    kind = filetype.guess(image_bytes)
    if kind is None or not kind.mime.startswith('image/'):
        raise ValueError("Could not determine image type or file is not an image")

    b64_str = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:image/{image_type};base64,{b64_str}"

def dataurl_to_image(dataurl: str) -> bytes:
    import base64
    
    if not dataurl.startswith('data:image/'):
        raise ValueError("Invalid data URL - must start with 'data:image/'")
    
    header, b64_data = dataurl.split(',', 1)
    return base64.b64decode(b64_data)

def get_time_elasped(dt, full=False) -> list:
  if isinstance(dt, str):
    try:
      ago = datetime.fromisoformat(dt)
    except Exception:
      ago = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
  elif isinstance(dt, datetime):
    ago = dt
  else:
    raise TypeError("dt must be a datetime or a datetime string")

  now = datetime.now(ago.tzinfo) if ago.tzinfo else datetime.now()
  delta = now - ago
  total_seconds = int(delta.total_seconds())
  if total_seconds <= 0:
    return []

  days = delta.days
  seconds = total_seconds - (days * 24 * 3600)

  years = days // 365
  days -= years * 365
  months = days // 30
  days -= months * 30
  weeks = days // 7
  days -= weeks * 7

  hours = seconds // 3600
  minutes = (seconds % 3600) // 60
  secs = seconds % 60

  parts_def = [
    (years, "year"),
    (months, "month"),
    (weeks, "week"),
    (days, "day"),
    (hours, "hour"),
    (minutes, "minute"),
    (secs, "second"),
  ]

  parts = []
  for value, name in parts_def:
    if value:
      parts.append(f"{value} {name}{"s" if value > 1 else ""}")

  if not full:
    parts = parts[:1]

  return parts

def time_elasped_string(dt, full=False) -> str:
    string = get_time_elasped(dt, full)
    return (", ").join(string) + " ago" if string else "just now"

def get_admin_code() -> int:
    try:
        with open("admin_code.txt", "r") as file:
            code = int(file.read().strip())
            return code
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": f"Admin code not set up properly: {str(e)}"})

def set_admin_code(new_code: int):
    try:
        with open("admin_code.txt", "w") as file:
            file.write(str(new_code))
          
    except Exception as e:
        print(f"Error setting admin code {e})")
                                                                 
def verify_admin(admin_id: str) -> bool:
    admin = Admin()
    admin.fromUUID(admin_id)
    admin_data = admin.fetch_admindata()
    if admin_data.isActive and not admin_data.probation:
        return True
    
    return False 

class User:
    def __init__(self):
        self.uuid = generate_uuid()

    def fetch_userdata(self):
        return UserData(
            id = self.uuid,
            username = self.username,
            email = self.email,
            JD = self.JD,
            confirm_email = self.confirm_email
        )

    def update_db(self):
        user_data = {
            "username": self.username,
            "age": self.age,
            "JD": self.JD,
            "confirm_email": self.confirm_email,
        }

        user = db.collection("users").document(self.uuid)
        if not user.get().exists:
            return JSONResponse(status_code=404, content={"error": "Invalid user ID"})

        user.update(user_data)
        return {"status": "success", "userdata": user_data}

    def add_user(self):
        user_data = {
            "username": self.username,
            "email": self.email,
            "psw": self.psw,
            "age": self.age,
            "JD": self.JD,
            "confirm_email": False,
            "sub": self.sub
        }

        try:
            existing_user = db.collection("users").where(field_path="email", op_string="==", value=self.email).get()
            if existing_user:
                return "Email already registered"

            db.collection("users").document(self.uuid).set(user_data)

            self.request_confirm_email()
            return "success"
        except Exception as e:
            raise HTTPException(status_code=500, detail=e)

    def from_register(self, form: RegisterForm):
        self.uuid = generate_uuid()
        self.username = form.username
        self.email = form.email
        self.psw = hash_password(form.psw)
        self.age = calculate_age(datetime.now())
        self.JD = datetime.now()
        self.confirm_email = False
        self.sub = form.sub

        return self.add_user()

    def from_discord_login(self):
        print("To be continued")

    def request_confirm_email(self):
        email_code = round(random.randint(100000, 999999))
        try:
            existing_request = db.collection("email_codes").document(self.uuid)
            if existing_request.get().exists:
                existing_request.delete()

            email_code_request = {
                "id": self.uuid,
                "datetime": datetime.now(),
                "digits": email_code
            }

            db.collection("email_codes").document(self.uuid).set(email_code_request)

            code_html = f"""<div style='display: flex;height: 61px;width: 249px;justify-content: space-between;align-items: center;flex-direction: row;line-height: 14px;'>{"".join(f"<div style='display: flex;height: 11px;padding: 19px 6px;border: 2px solid #6f67d9;border-radius: 7px;background-color: #f5f5f5;color: #000;font-size: 40px;'>{str(email_code)[i]}</div>" for i in range(len(str(email_code))))}</div>"""

            html_content = [
                {
                    "type": "table",
                    "content": [    
                        {
                            "type": "table",
                            "content": [
                                # {"type": "image", "content": "image/logo.png"},
                                {"type": "header", "content": "Verify Your Email Address"},
                                {"type": "text", "content": "We just need to verify your email address to activate your SurfNetwork account. Here's your verification code:"},
                                {"type": "html", "content": code_html},
                                {"type": "html", "content": "This code expires within 5 minutes"},
                                {"type": "text", "content": "Only enter this code on the SurfNetwork website. Don't share it with anyone. We'll never ask for it outside any of our platforms."},
                                {"type": "text", "content": "Welcome aboard!"},
                                {"type": "text", "content": "SurfNetwork Team"}
                            ]
                        }
                    ]
                },
                {
                    "type": "table",
                    "content": [
                        {"type": "text", "content": "This email was sent to you by the SurfNetwork because you signed up for a SurfNetwork account.break-linePlease let us know if you feel that this email was sent to you by error."},
                        {"type": "text", "content": "© 2025 SurfNetwork"},
                        {"type": "list", "content": [
                            {"type": "hyperlink", "content": "Privacy Policy", "link": "#"},
                            {"type": "hyperlink", "content": "Personal Data Protection and Privacy Policy", "link": "#"},
                            {"type": "hyperlink", "content": "Acceptable Use Policy", "link": "#"},
                        ]}
                    ]
                }
            ]

            send_html_email(to_email=self.email, to_name=self.username, subject="Verify your email - SurfNetwork", html_content=html_content)

        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": str(e)})

    def from_login(self, form: LoginForm):

        query = db.collection("users").where(field_path="email", op_string="==", value=form.email).get()
        if not query:
            raise HTTPException(status_code=404, detail={"error": "Invalid email, please register with this username"})

        user_data = query[0].to_dict()
        if user_data is None:
            raise HTTPException(status_code=404, detail={"error": "User data not found"})

        if not verify_password(form.psw, user_data["psw"]):
            raise HTTPException(status_code=400, detail={"error": "Incorrect password"})

        self.uuid = query[0].id
        self.username = user_data["username"]
        self.email = user_data["email"]
        self.psw = user_data["psw"]
        self.age = calculate_age(user_data["JD"])
        self.JD = user_data["JD"]
        self.confirm_email = user_data["confirm_email"]
        self.player_id = user_data["player_id"]

        return self.fetch_userdata().model_dump()

    def from_userdata(self, userdata: UserData, should_update: bool = False):
        self.uuid = userdata.id
        self.username = userdata.username
        self.email = userdata.email
        self.age = calculate_age(userdata.JD)
        self.JD = userdata.JD
        self.confirm_email = userdata.confirm_email
        self.player_id = userdata.player_id

        if should_update:
            return self.update_db()

    def fromUUID(self, uuid: str):
        self.uuid = uuid
        query = db.collection("users").document(self.uuid).get()
        if not query:
            raise HTTPException(status_code=404, detail={"error": "Invalid user ID"})

        user = query.to_dict()
        if user is None:
            raise HTTPException(status_code=500, detail={"error": "User data not found"})
        
        self.username = user["username"]
        self.email = user["email"]
        self.psw = user["psw"]
        self.age = user["age"]
        self.JD = user["JD"]
        self.confirm_email : bool = user["confirm_email"]
        if user["player_id"] is None:
            self.player_id = ""
        else:
            self.player_id = user["player_id"]
        
        return self.fetch_userdata()

    def fetch_data(self, data: str):
        uuid = self.uuid
        query = db.collection(data).document(uuid).get()
        if not query:
            raise HTTPException(status_code=404, detail={"error": f"Invalid user ID"})

        result = query.to_dict()
        if result is None:
            raise HTTPException(status_code=500, detail={"error": f"cannot fetch {data} with user ID"})

        return result

    def request_password_reset(self):
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

        send_html_email(to_email=self.email, to_name=self.username, subject="Verify your email - SurfNetwork", html_content=html_content)

        user_reset_request = {
            "datetime": datetime.now(),
            "reset_code": reset_code
        }

        try:
            existing_request = db.collection("reset_psw_request").document(self.uuid)
            if existing_request.get().exists:
                existing_request.delete()

            db.collection("reset_psw_request").document(self.uuid).set(user_reset_request)
            
            return {"status": "success"}
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    def validate_password_request(self, reset_code: int):
        reset_key = generate_uuid()
        try:
            code = self.fetch_data("reset_psw_request")

            now = datetime.now()
            minutes = now.minute - code["datetime"].minute - (now.second < code["datetime"].second)
            if minutes >= 5:
                return JSONResponse(status_code=400, content={"error": "Code expired, request another one"})
            
            else:
                if code["reset_code"] == reset_code:
                    try:
                        user_reset_key = {
                            "id": self.uuid,
                            "datetime": datetime.now(),
                            "reset_key": reset_key
                        }

                        existing_request = db.collection("reset_psw_key").document(self.uuid)
                        if existing_request.get().exists:
                            existing_request.delete()

                        request = db.collection("reset_psw_key").document(self.uuid).set(user_reset_key)
                        return {"status": "success", "reset_key": reset_key}

                    except Exception as e:
                        return JSONResponse(status_code=500, content={"error": str(e)})
                                
                else:
                    return JSONResponse(status_code=400, content={"error": "Invalid code"})

        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    def update_psw(self, change_key: str, new_password_unsafe: str):
        new_password = hash_password(new_password_unsafe)

        try:
            reset_key = self.fetch_data("reset_key")

            now = datetime.now()
            minutes = now.minute - reset_key["datetime"].minute - (now.month < reset_key["datetime"])
            if minutes >= 5:
                return JSONResponse(status_code=400, content={"error": "Session expired, request another one"})

            else:
                if change_key == reset_key["reset_key"]:
                    user_data = {
                        "psw": new_password
                    }

                    user = db.collection("users").document(self.uuid)
                    if not user.get().exists:
                        return JSONResponse(status_code=404, content={"error": "Invalid user ID"})

                    user.update(user_data)
                    return {"status": "success"}

        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    # TODO rework this module   
    """
    def submit_quest(self):
        user_ref = db.collection("users_progress").document(self.uuid)
        user_data = user_ref.get().to_dict() or {
            "completed_quests": [],
            "current_streak": 0,
            "xp": 0,
            "badges": [],
            "last_quest_date": None   
        }

        today = date.today()
        last_date = user_data["last_quest_date"]
        quest_id = f"quest_{today.strftime('%Y%m%d')}"

        if quest_id in user_data["completed_quests"]:
            raise HTTPException(400, "Quest already completed.")

        yesterday = today - timedelta(days=1)
        if last_date == yesterday.isoformat():
            user_data["current_streak"] = 1
        
        else:
            user_data["current_streak"] = 1

        quest = db.collection("quests").document(today.isoformat()).get()
        if quest.exists:
            data = quest.to_dict()

            if data is None:
                raise HTTPException(status_code=404, detail="Quest data not found")
            
            xp_reward = data["reward"]
        else:
            xp_reward = 5
            data = {
                "id": quest_id,
                "tasks": "Complete today's quest",
                "reward": xp_reward
            }
        
        user_data["completed_quests"].append(quest_id)
        user_data["xp"] += xp_reward
        user_data["last_quest_date"] = today.isoformat()

        for badge, rule in BADGE_RULES.items():
            if badge not in user_data["badges"] and rule(user_data):
                user_data["badges"].append(badge)

        user_ref.set(user_data)
        return JSONResponse(status_code=200, content={"message": "Quest submitted", "badges": user_data["badges"]})
    """

    def submit_daily_quest(self, quest_id: str):
        user_ref = db.collection("users_progress").document(self.uuid)
        user_data = user_ref.get().to_dict() or {
            "completed_quests": [],
            "current_streak": 0,
            "xp": 0,
            "badges": [],
            "last_quest_date": None   
        }

        today = date.today()
        last_date = user_data["last_quest_date"]

        if quest_id in user_data["completed_quests"]:
            raise HTTPException(400, "Quest already completed.")

        yesterday = today - timedelta(days=1)
        if last_date == yesterday.isoformat():
            user_data["current_streak"] = 1
        
        else:
            user_data["current_streak"] = 1

        quest = db.collection("quests").document(today.isoformat()).get()
        if quest.exists:
            data = quest.to_dict()

            if data is None:
                raise HTTPException(status_code=404, detail="Quest data not found")
            
            xp_reward = data["reward"]
        else:
            xp_reward = 5
            data = {
                "id": quest_id,
                "tasks": "Complete today's quest",
                "reward": xp_reward
            }
        
        user_data["completed_quests"].append(quest_id)
        user_data["xp"] += xp_reward
        user_data["last_quest_date"] = today.isoformat()

        for badge, rule in BADGE_RULES.items():
            if badge not in user_data["badges"] and rule(user_data):
                user_data["badges"].append(badge)

        user_ref.set(user_data)
        return JSONResponse(status_code=200, content={"message": "Quest submitted", "badges": user_data["badges"]})

    def submit_weekly_quest(self, quest_id: str):
        user_ref = db.collection("users_progress").document(self.uuid)
        user_data = user_ref.get().to_dict() or {
            "completed_quests": [],
            "current_streak": 0,
            "xp": 0,
            "badges": [],
            "last_quest_date": None   
        }

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_start_str = week_start.isoformat()

        if quest_id in user_data["completed_quests"]:
            raise HTTPException(400, "Quest already completed.")

        quest = db.collection("quests").document(week_start_str).get()
        if quest.exists:
            data = quest.to_dict()

            if data is None:
                raise HTTPException(status_code=404, detail="Quest data not found")
            
            xp_reward = data["reward"]
        else:
            xp_reward = 10
            data = {
                "id": quest_id,
                "tasks": "Complete this week's quest",
                "reward": xp_reward
            }
        
        user_data["completed_quests"].append(quest_id)
        user_data["xp"] += xp_reward

        for badge, rule in BADGE_RULES.items():
            if badge not in user_data["badges"] and rule(user_data):
                user_data["badges"].append(badge)

        user_ref.set(user_data)
        return JSONResponse(status_code=200, content={"message": "Quest submitted", "badges": user_data["badges"]})

    def redeem_reward(self, reward_id: str):
        reward_doc = db.collection("rewards").document(reward_id).get()
        if not reward_doc.exists:
            raise HTTPException(status_code=404, detail="Reward not found")

        reward = reward_doc.to_dict()
        if reward is None:
            raise HTTPException(status_code=404, detail="Reward data not found")

        user_ref = db.collection("user_progress").document(self.uuid)
        user_data = user_ref.get().to_dict()

        if user_data is None:
            raise HTTPException(status_code=404, detail="User progress not found")

        if user_data["xp"] < reward["cost"]:
            raise HTTPException(status_code=400, detail="Not enough XP")

        user_data["xp"] -= reward["cost"]
        user_data.setdefault("redeem_rewards", []).append(reward_id)

        user_ref.set(user_data)
        return JSONResponse(status_code=200, content={"message": "Reward redeemed"})

class Admin:
    def __init__(self):
        self.id = generate_uuid()
        self.logTime = datetime.now()
        self.color = '#21b4b4'

    def fetch_admindata(self):
        return AdminData(
            id = self.uuid,
            username = self.username,
            email = self.email,
            role = self.role,
            badges = self.badges,
            color = self.color,
            logTime = self.logTime,
            isActive = self.isActive,
            probation = self.probation
        )

    def update_db(self):
        user_data = {
            "username": self.username,
            "role": self.role,
            "badges": self.badges,
            "color": self.color,
            "logTime": self.logTime,
            "isActive": self.isActive,
            "probation": self.probation
        }

        user = db.collection("admins").document(self.uuid)
        if not user.get().exists:
            return JSONResponse(status_code=404, content={"error": "Invalid admin ID"})

        user.update(user_data)
        return {"status": "success", "admindata": user_data}

    def add_admin(self):
        user_data = {
            "username": self.username,
            "email": self.email,
            "psw": self.psw,
            "role": self.role,
            "badges": self.badges,
            "color": self.color,
            "logTime": self.logTime,
            "isActive": self.isActive,
            "probation": self.probation
        }

        try:
            existing_admin = db.collection("admins").where(field_path="email", op_string="==", value=self.email).get()
            if existing_admin:
                return {"error" :"Email already registered"}

            db.collection("admins").document(self.uuid).set(user_data)
            return {"status": "success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=e)

    def from_register(self, form: AdminRegisterForm):
        admin_code = form.admin_code
        if admin_code != get_admin_code():
            raise HTTPException(status_code=403, detail={"error": "Invalid admin code"})
        
        self.uuid = generate_uuid()
        self.username = form.username
        self.email = form.email
        self.psw = hash_password(form.psw)
        self.role = "admin"
        self.badges = ["admin"]
        self.logTime = datetime.now()
        self.isActive = False
        self.probation = False

        return self.add_admin() 

    def from_login(self, form: AdminLoginForm):

        query = db.collection("admins").where(field_path="email", op_string="==", value=form.email).get()
        if not query:
            raise HTTPException(status_code=404, detail={"error": "Invalid email, please apply with this email or contact an admin to help resolve the issue"})

        admin_data = query[0].to_dict()
        if admin_data is None:
            raise HTTPException(status_code=404, detail={"error": "Admin data not found"})

        if not verify_password(form.psw, admin_data["psw"]):
            raise HTTPException(status_code=400, detail={"error": "Incorrect password"})

        self.uuid = query[0].id
        self.username = admin_data["username"]
        self.email = admin_data["email"]
        self.psw = admin_data["psw"]
        self.role = admin_data["role"]
        self.badges = admin_data["badges"]
        self.color = admin_data["color"]
        self.logTime = datetime.now()
        self.isActive = True
        self.probation = admin_data["probation"]

        self.update_db()

        return self.fetch_admindata().model_dump()

    def from_userdata(self, admindata: AdminData, should_update: bool = False):
        self.uuid = admindata.id
        self.username = admindata.username
        self.email = admindata.email
        self.role = admindata.role
        self.badge = admindata.badges
        self.color = admindata.color
        self.logTime = admindata.logTime
        self.isActive = admindata.isActive
        self.probation = admindata.probation

        if should_update:
            return self.update_db()

    def fromUUID(self, uuid: str):
        self.uuid = uuid
        query = db.collection("admins").document(self.uuid).get()
        if not query:
            raise HTTPException(status_code=404, detail={"error": "Invalid admin ID"})

        admin = query.to_dict()
        if admin is None:
            raise HTTPException(status_code=404, detail={"error": "Admin data not found"})
        
        self.username = admin["username"]
        self.email = admin["email"]
        self.role = admin["role"]
        self.badges = admin["badges"]
        self.color = admin["color"]
        self.logTime = admin["logTime"]
        self.isActive = admin["isActive"]
        self.probation = admin["probation"]
        
        return self.fetch_admindata()

    def fetch_data(self, data: str):
        uuid = self.uuid
        query = db.collection(data).document(uuid).get()
        if not query:
            raise HTTPException(status_code=404, detail={"error": f"Invalid admin ID"})

        result = query.to_dict()
        if result is None:
            raise HTTPException(status_code=500, detail={"error": f"cannot fetch {data} with admin ID"})

        return result
