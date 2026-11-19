
"""
Module 2.1 - Pydantic basics: a ShopKart Product model.

Real life problem: data coming into an app is often WRONG.
  - a seller uploads a catalogue with price = "free"
  - a mobile app sends stock = "ten"
  - a field is simply missing
Pydantic checks the data the moment you create the object,
so bad data never reaches your database or payment code.
"""
import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ValidationError   # pip install pydantic

DATA_FILE = Path(__file__).parent / "data" / "seller_upload.json"


class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int = 0                       # default value if missing
    category: str = "general"            # default value if missing
    description: Optional[str] = None    # allowed to be missing / None


def demo_valid_product():
    print("=== 1. A valid product ===")
    p = Product(id=101, name="Wireless Mouse", price=799.0, stock=50)
    print(p)
    print("Name:", p.name, "| Price:", p.price, "| Category (default):", p.category)


def demo_type_conversion():
    print("\n=== 2. Automatic type conversion ===")
    # Data from an HTML form or a CSV - EVERYTHING arrives as text
    form_data = {"id": "102", "name": "Cotton T-Shirt", "price": "499.50", "stock": "120"}
    p = Product(**form_data)
    print(p)
    print("type(price) =", type(p.price).__name__, "| type(stock) =", type(p.stock).__name__)


def demo_invalid_product():
    print("\n=== 3. Bad data is rejected with clear messages ===")
    bad_data = {"id": "abc", "price": "free", "stock": 10}   # name is missing too
    try:
        Product(**bad_data)
    except ValidationError as e:
        print(f"Found {e.error_count()} errors:")
        for err in e.errors():
            field = ".".join(str(x) for x in err["loc"])
            print(f"  - {field}: {err['msg']}")


def validate_seller_upload():
    print("\n=== 4. Real case: bulk catalogue upload by a seller ===")
    with open(DATA_FILE, encoding="utf-8") as f:
        rows = json.load(f)

    accepted, rejected = [], []
    for row_number, row in enumerate(rows, start=1):
        try:
            product = Product.model_validate(row)        # same as Product(**row)
            accepted.append(product)
        except ValidationError as e:
            first_error = e.errors()[0]
            rejected.append((row_number, first_error["loc"][0], first_error["msg"]))

    print(f"Accepted {len(accepted)} / {len(rows)} rows")
    for p in accepted:
        print(f"  OK   {p.id} {p.name} Rs.{p.price}")
    for row_number, field, msg in rejected:
        print(f"  FAIL row {row_number}: {field} -> {msg}")


if __name__ == "__main__":
    demo_valid_product()
    demo_type_conversion()
    demo_invalid_product()
    validate_seller_upload()
