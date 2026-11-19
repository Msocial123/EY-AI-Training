"""
product_service/schemas.py
--------------------------
Pydantic schemas = the "contract" of our API.
They decide what data is ALLOWED IN (request) and what GOES OUT (response).

Real-life idea: When a seller on Amazon adds a product, Amazon rejects it if
the price is negative, the title is empty, or the selling price is higher
than the MRP. That checking is exactly what these classes do - automatically.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


# --- [2.1] Enum: only fixed values allowed ---
class Category(str, Enum):
    electronics = "electronics"
    fashion = "fashion"
    grocery = "grocery"
    books = "books"
    home = "home"


# --- [2.2] Nested schema: Seller lives INSIDE a Product ---
class Seller(BaseModel):
    name: str = Field(min_length=2, max_length=60, examples=["RetailNet"])
    city: str = Field(min_length=2, examples=["Bengaluru"])
    rating: float = Field(default=4.0, ge=1, le=5, description="Seller rating 1-5")


# --- [2.3] Request schema: what the client SENDS to create a product ---
class ProductCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100, examples=["Apple iPhone 15 (128 GB)"])
    description: str | None = Field(default=None, max_length=500)
    category: Category
    price: float = Field(gt=0, description="Selling price in INR")
    mrp: float = Field(gt=0, description="Maximum Retail Price in INR")
    tags: list[str] = Field(default_factory=list, max_length=10)
    seller: Seller  # <-- nested model

    # Field validator: clean ONE field
    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.split())  # "  iPhone    15 " -> "iPhone 15"

    @field_validator("tags")
    @classmethod
    def lowercase_tags(cls, tags: list[str]) -> list[str]:
        return sorted({t.strip().lower() for t in tags if t.strip()})

    # Model validator: check a rule that needs MORE THAN ONE field
    @model_validator(mode="after")
    def price_not_above_mrp(self):
        if self.price > self.mrp:
            raise ValueError("price cannot be greater than mrp")
        return self


# --- [2.4] Update schema: every field optional (for PATCH) ---
class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    mrp: float | None = Field(default=None, gt=0)
    tags: list[str] | None = None


# --- [2.5] Response schema: what the API SENDS BACK ---
class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    category: Category
    price: float
    mrp: float
    tags: list[str]
    seller: Seller
    created_at: datetime

    @computed_field  # calculated on the fly, never stored
    @property
    def discount_percent(self) -> int:
        return round((self.mrp - self.price) / self.mrp * 100)


class ProductPage(BaseModel):
    """Paginated list response - like page 1, 2, 3 on a shopping site."""
    total: int
    page: int
    size: int
    items: list[ProductOut]
