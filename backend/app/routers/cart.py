# app/routers/cart.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.db import db
from typing import List, Optional
import random
import uuid

router = APIRouter()

class Product(BaseModel):
    id: Optional[str] = str(uuid.uuid4())
    name: str
    price: float
    badge: Optional[str]
    icon: Optional[str]
    features: Optional[List[str]]
    description: Optional[str]
    category: Optional[str]

class CartList(BaseModel):
    list: List[Product]

@router.get(path="/carts/{cart_id}", response_model=dict)
def get_cart(cart_id: str):
    doc = db.collection("carts").document(cart_id).get()
    if doc.exists:
        cart = doc.to_dict()
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
