"""
product_service/main.py   ->   ShopKart PRODUCT CATALOG microservice (FastAPI)

Run:   uvicorn product_service.main:app --reload --port 8001
Docs:  http://127.0.0.1:8001/docs      (Swagger UI - try every API in the browser)

This ONE file teaches the FastAPI essentials:
    path parameters, query parameters, request body, status codes,
    response models, errors (HTTPException) and middleware.
"""
import json
import os
from typing import Literal

from fastapi import FastAPI, HTTPException, Path, Query, Request, Response, status
from pydantic import ValidationError

from product_service import database as db
from product_service.schemas import Category, ProductCreate, ProductOut, ProductPage, ProductUpdate

# --- [1.1] Create the app + health check ---
app = FastAPI(
    title="ShopKart Product Service",
    description="Product catalog microservice for the ShopKart e-commerce platform",
    version="1.0.0",
)

INSTANCE_NAME = os.getenv("INSTANCE_NAME", "product-1")


@app.get("/health", tags=["ops"])
def health():
    """Load balancers call this every few seconds: 'are you alive?'"""
    return {"service": "product-service", "instance": INSTANCE_NAME, "status": "ok"}


# --- [1.2] Path parameter: /products/{product_id} ---
@app.get("/products/{product_id}", response_model=ProductOut, tags=["products"])
def get_product(product_id: int = Path(gt=0, description="ID of the product")):
    """Product detail page -> e.g. shopkart.com/products/1"""
    product = db.PRODUCTS.get(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    return product


# --- [1.3] Query parameters: filters, search, sorting, pagination ---
@app.get("/products", response_model=ProductPage, tags=["products"])
def list_products(
    category: Category | None = None,
    search: str | None = Query(default=None, min_length=2, description="Search in name"),
    min_price: float = Query(default=0, ge=0),
    max_price: float | None = Query(default=None, gt=0),
    sort_by: Literal["price_asc", "price_desc", "name"] = "name",
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
):
    """Search/listing page -> /products?category=electronics&max_price=80000&sort_by=price_asc"""
    items = list(db.PRODUCTS.values())

    if category:
        items = [p for p in items if p["category"] == category.value]
    if search:
        items = [p for p in items if search.lower() in p["name"].lower()]
    items = [p for p in items if p["price"] >= min_price]
    if max_price is not None:
        items = [p for p in items if p["price"] <= max_price]

    if sort_by == "price_asc":
        items.sort(key=lambda p: p["price"])
    elif sort_by == "price_desc":
        items.sort(key=lambda p: p["price"], reverse=True)
    else:
        items.sort(key=lambda p: p["name"])

    start = (page - 1) * size
    return {"total": len(items), "page": page, "size": size, "items": items[start:start + size]}


# --- [1.4] Request body + 201 Created ---
@app.post(
    "/products",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    tags=["products"],
)
def create_product(product: ProductCreate):
    """Seller dashboard -> 'Add new product'. Body is validated by Pydantic first."""
    for existing in db.PRODUCTS.values():
        if existing["name"].lower() == product.name.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A product with this name already exists",
            )
    return db.add_product(product.model_dump(mode="json"))


# --- [1.5] Update: PUT (replace all) and PATCH (change some fields) ---
@app.put("/products/{product_id}", response_model=ProductOut, tags=["products"])
def replace_product(product: ProductCreate, product_id: int = Path(gt=0)):
    existing = db.PRODUCTS.get(product_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    existing.update(product.model_dump(mode="json"))
    return existing


@app.patch("/products/{product_id}", response_model=ProductOut, tags=["products"])
def update_product(changes: ProductUpdate, product_id: int = Path(gt=0)):
    """Flash sale! Change only the price: PATCH /products/1  body: {"price": 64999}"""
    existing = db.PRODUCTS.get(product_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    merged = {**existing, **changes.model_dump(exclude_unset=True)}
    try:
        checked = ProductCreate(**merged)  # re-run ALL rules (price <= mrp etc.)
    except ValidationError as err:
        raise HTTPException(status_code=422, detail=json.loads(err.json(include_url=False)))
    existing.update(checked.model_dump(mode="json"))
    return existing


# --- [1.6] Delete -> 204 No Content ---
@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["products"])
def delete_product(product_id: int = Path(gt=0)):
    if db.PRODUCTS.pop(product_id, None) is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- [1.7] Middleware: add a header to EVERY response ---
@app.middleware("http")
async def add_instance_header(request: Request, call_next):
    """Tells us WHICH copy of the service answered (useful behind a load balancer)."""
    response = await call_next(request)
    response.headers["X-Instance"] = INSTANCE_NAME
    return response
