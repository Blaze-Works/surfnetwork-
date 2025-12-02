# app/models/cart_model.py

from pydantic import BaseModel
from typing import Optional, List
import uuid

class Product(BaseModel):
    id: Optional[str] = str(uuid.uuid4())
    name: str
    price: float
    badge: Optional[str]
    icon: Optional[str]
    features: Optional[List[str]]
    description: Optional[str]
    category: Optional[str]
    qty: int = 1

class CartList(BaseModel):
    list: List[Product]

class CheckoutRequest(BaseModel):
    user_id: str
    cart_id: str