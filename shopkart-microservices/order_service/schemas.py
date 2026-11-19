"""
order_service/schemas.py
------------------------
Order = the most important object in e-commerce. It is DEEPLY nested:

    OrderCreate
      |- customer_name, email, phone
      |- items: list[OrderItem]          <- list of nested models
      |- shipping_address: Address       <- nested model
      |- payment_mode: "UPI" | "CARD" | "COD"
"""
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

COD_LIMIT = 50_000  # Business rule: Cash on Delivery not allowed above Rs 50,000


# --- [2.6] Nested schemas: Address and OrderItem ---
class Address(BaseModel):
    line1: str = Field(min_length=5, examples=["Flat 302, Sai Residency"])
    city: str = Field(min_length=2, examples=["Kadapa"])
    state: str = Field(min_length=2, examples=["Andhra Pradesh"])
    pincode: str = Field(pattern=r"^[1-9][0-9]{5}$", examples=["516003"])


class OrderItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=10, description="Max 10 units per product")


# --- [2.7] The order request: lists + nested models + business rules ---
class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=60)
    email: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$", examples=["ravi@example.com"])
    phone: str = Field(pattern=r"^[6-9][0-9]{9}$", examples=["9876543210"])
    items: list[OrderItem] = Field(min_length=1, max_length=20)
    shipping_address: Address
    payment_mode: Literal["UPI", "CARD", "COD"] = "UPI"

    @model_validator(mode="after")
    def no_duplicate_products(self):
        ids = [item.product_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("same product_id appears twice - increase quantity instead")
        return self


# --- [2.8] Response schemas ---
class OrderStatus(str, Enum):
    PLACED = "PLACED"          # saved, waiting for the worker
    CONFIRMED = "CONFIRMED"    # stock reserved by inventory service
    FAILED = "FAILED"          # out of stock / could not process
    CANCELLED = "CANCELLED"


class OrderLine(BaseModel):
    product_id: int
    name: str
    unit_price: float
    quantity: int
    line_total: float


class OrderOut(BaseModel):
    id: int
    customer_name: str
    email: str
    status: OrderStatus
    payment_mode: str
    lines: list[OrderLine]
    total_amount: float
    shipping_address: Address
    created_at: datetime
    note: str | None = None


class StatusUpdate(BaseModel):
    status: OrderStatus
    note: str | None = None
