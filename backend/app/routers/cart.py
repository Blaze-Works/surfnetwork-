# app/routers/cart.py

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from app.core.db import db
from app.core.mc import send_request_to_plugin, get_playername, get_playerid
from app.core.utils import User
from app.models.cart_model import Product, CartList, CheckoutRequest
from typing import List, Optional
import random
import uuid
import httpx
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

TEBEX_API_KEY = os.getenv("TEBEX_API_KEY")
TEBEX_API_URL = os.getenv("TEBEX_API_uRL")

@router.get(path="/carts/{cart_id}", response_model=dict)
def get_cart(cart_id: str):
    doc = db.collection("carts").document(cart_id).get()
    if doc.exists:
        cart : dict = doc.to_dict()
        return cart.items
    else:
        raise HTTPException(status_code=404, detail={"error": "Cart not found"})

@router.put(path="/carts/{cart_id}", response_model=dict)
def put_into_cart(cart_id: str, cart_list: CartList):
    cart = [
        cart_list.list[i].dict() for i in range(len(cart_list.list))
    ]
    try:
        db.collection("carts").document(cart_id).set(cart)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

    return {"message", "Added to cart"}

@router.get(path="/products", response_model=dict)
def list_products():
    docs = db.collection("products").stream()
    if docs is None:
        raise HTTPException(status_code=404, detail={"error": "No products found"})
    products = [doc.to_dict() for doc in docs]
    return {"products": products}

@router.put(path="/products/add", response_model=dict)
def add_product(item: Product):
    item = item.dict()
    print(item)
    try:
        db.collection("products").document(item.get("id")).set(item)
        return {"message": "Item added to products"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.post("/checkout", response_model=dict)
async def create_checkout(data: CheckoutRequest):
    user = User()
    user.fromUUID(data.user_id)
    userdata = user.fetch_userdata()
    username = get_playername(user)
    uuid = get_playerid(user)

    cart : List[Product] = get_cart(data.cart_id)

    payload = {
        "baasket": {
            "email": userdata.email,
            "complete_url": "https://surfnetwork-api.onrender.com/checkout/complete",
            "return_url": "https://surfnetwork-api.onrender.com/checkout/success",
            "custom": {
                "player": {"username": username, "uuid": uuid},
                "user": data.user_id
            }
        },
        "items": [
            {"package": {"name": item.name, "price": item.price}} for item in cart
        ]
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{TEBEX_API_URL}/checkout",
            headers={"X-Tebex-Secret": TEBEX_API_KEY},
            json=payload
        )
        res.raise_for_status()
        checkout_data = res.json()

    print(checkout_data)
    return {"checkout_url": checkout_data["data"]["urls"]["checkout"]}

# --- Tebex webhook (payment completed) ---
@router.post("/webhook")
async def tebex_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    # Validate event type
    if body.get("event") == "payment.completed":
        player = body["player"]["username"]
        uuid = body["player"]["uuid"]
        packages = body["packages"]

        # Run reward in background
        payload = {
            "action": "reward",
            "player": player,
            "uuid": uuid,
            "packages": [
                {"id": p["id"], "name": p["name"]} for p in packages
            ]
        }
        background_tasks.add_task(send_request_to_plugin, player, uuid, packages)

    return {"status": "ok"}

