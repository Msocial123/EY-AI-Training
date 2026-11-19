"""
Module 2.2 - Business rules with Field(...) and validators.

Types alone are not enough. "price = -50" IS a float, but it is wrong.
Real ShopKart rules:
  - price must be > 0, stock can never be negative
  - name 3 to 100 characters, cleaned up (extra spaces, Title Case)
  - SKU format like  SK-ELE-0001
  - category only from a fixed list
  - Indian law: selling price can NOT be more than MRP
"""
from enum import Enum

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class Category(str, Enum):
    ELECTRONICS = "electronics"
    FASHION = "fashion"
    HOME = "home"
    GROCERY = "grocery"


class Product(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=3, max_length=100)
    sku: str = Field(pattern=r"^SK-[A-Z]{3}-\d{4}$")
    category: Category
    mrp: float = Field(gt=0)
    price: float = Field(gt=0)
    stock: int = Field(default=0, ge=0)

    # Runs on ONE field. Good for cleaning / checking a single value.
    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())        # remove extra spaces
        return cleaned.title()                   # "wireless   mouse" -> "Wireless Mouse"

    # Runs AFTER all fields are valid. Good for rules that compare fields.
    @model_validator(mode="after")
    def price_not_above_mrp(self):
        if self.price > self.mrp:
            raise ValueError(f"price {self.price} cannot be more than MRP {self.mrp}")
        return self

    @property
    def discount_percent(self) -> float:
        return round((self.mrp - self.price) / self.mrp * 100, 1)


def try_product(title, data):
    print(f"\n--- {title} ---")
    try:
        p = Product(**data)
        print(f"OK  -> {p.name} | {p.category.value} | Rs.{p.price} "
              f"(MRP {p.mrp}, {p.discount_percent}% off)")
    except ValidationError as e:
        for err in e.errors():
            field = ".".join(str(x) for x in err["loc"]) or "(whole product)"
            print(f"ERR -> {field}: {err['msg']}")


if __name__ == "__main__":
    good = {"id": 101, "name": "  wireless   mouse ", "sku": "SK-ELE-0001",
            "category": "electronics", "mrp": 999, "price": 799, "stock": 50}
    try_product("Valid product (name gets cleaned)", good)

    try_product("Negative price and stock", {**good, "price": -50, "stock": -3})
    try_product("Wrong SKU format", {**good, "sku": "ELE1"})
    try_product("Unknown category", {**good, "category": "toys"})
    try_product("Price above MRP (illegal in India)", {**good, "price": 1299})
    try_product("Name too short", {**good, "name": "TV"})
