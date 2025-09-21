# app/core/db.py

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import base64

load_dotenv()

firebase_key_base64 = os.getenv("FIREBASE_KEY")

if not firebase_key_base64:
    raise ValueError("FIREBASE_KEY environment variable is not set.")

decoded_key = base64.b64decode(firebase_key_base64)
service_account_info = json.loads(decoded_key)

if not firebase_admin._apps:
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)

db = firestore.client()