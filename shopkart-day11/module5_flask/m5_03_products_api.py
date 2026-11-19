"""
Module 5.3 - A lightweight REST API: Flask + Pydantic + Logging + Error handling.
Everything from today, in ONE file.

Run:   python m5_03_products_api.py
Test:  use curl commands from the commands sheet, or api_requests.http in VS Code

  GET    /api/products              list (filters: ?category=  ?max_price=)
  GET    /api/products/<id>         one product
  POST   /api/products              create  (validated by Pydantic)
  PATCH  /api/products/<id>         update some fields
  DELETE /api/products/<id>         delete
"""
import logging
import time
from typing import Optional

from flask import Flask, g, jsonify, request
from pydantic import BaseModel, Field, ValidationError
from werkzeug.exceptions import HTTPException

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("shopkart.api")

app = Flask(__name__)
app.json.sort_keys = False
app.json.compact = False      # pretty JSON even when debug is off (easier to read in class)


# ---------- Pydantic schemas ----------
class ProductCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    price: float = Field(gt=0)
    stock: int = Field(default=0, ge=0)
    category: str = Field(min_length=2)


class ProductUpdate(BaseModel):            # every field optional -> partial update
    name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    category: Optional[str] = None


# ---------- "Database" ----------
PRODUCTS = {
    101: {"id": 101, "name": "Wireless Mouse", "price": 799.0, "stock": 50, "category": "electronics"},
    102: {"id": 102, "name": "Cotton T-Shirt", "price": 499.0, "stock": 120, "category": "fashion"},
}


# ---------- Custom error + handlers ----------
class NotFoundError(Exception):
    pass


@app.errorhandler(NotFoundError)
def handle_not_found(e):
    return jsonify(error="not_found", message=str(e)), 404


@app.errorhandler(ValidationError)
def handle_validation(e):
    details = [{"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]}
               for err in e.errors()]
    return jsonify(error="validation_failed", details=details), 422


@app.errorhandler(Exception)
def handle_unexpected(e):
    if isinstance(e, HTTPException):          # normal Flask errors: 404 wrong URL, 405 ...
        return jsonify(error=e.name, message=e.description), e.code
    logger.exception("Unexpected error")                      # full traceback in logs
    return jsonify(error="internal_error", message="Something went wrong"), 500


# ---------- Request logging (runs around EVERY request) ----------
@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def log_request(response):
    ms = (time.perf_counter() - g.start) * 1000
    logger.info("%s %s -> %s (%.1f ms)", request.method, request.full_path.rstrip("?"),
                response.status_code, ms)
    return response


# ---------- Routes ----------
def get_or_404(product_id):
    if product_id not in PRODUCTS:
        raise NotFoundError(f"Product {product_id} not found")
    return PRODUCTS[product_id]


@app.get("/api/products")
def list_products():
    category = request.args.get("category")
    max_price = request.args.get("max_price", type=float)
    items = list(PRODUCTS.values())
    if category:
        items = [p for p in items if p["category"] == category]
    if max_price is not None:
        items = [p for p in items if p["price"] <= max_price]
    return jsonify(count=len(items), items=items)


@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    return jsonify(get_or_404(product_id))


@app.post("/api/products")
def create_product():
    data = ProductCreate.model_validate(request.get_json(silent=True) or {})  # may raise -> 422
    new_id = max(PRODUCTS, default=100) + 1
    product = {"id": new_id, **data.model_dump()}
    PRODUCTS[new_id] = product
    logger.info("Created product %s (%s)", new_id, product["name"])
    return jsonify(product), 201


@app.patch("/api/products/<int:product_id>")
def update_product(product_id):
    product = get_or_404(product_id)
    changes = ProductUpdate.model_validate(request.get_json(silent=True) or {})
    product.update(changes.model_dump(exclude_unset=True))   # only fields actually sent
    return jsonify(product)


@app.delete("/api/products/<int:product_id>")
def delete_product(product_id):
    get_or_404(product_id)
    del PRODUCTS[product_id]
    return "", 204


@app.get("/api/crash")
def crash():
    """Demo only: shows that unexpected bugs return clean JSON + get logged."""
    return 1 / 0


if __name__ == "__main__":
    app.run(port=5005, debug=False)    # debug=False so our 500 handler is used
