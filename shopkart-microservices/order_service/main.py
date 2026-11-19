"""
order_service/main.py   ->   ShopKart ORDER microservice (FastAPI)

Run:   uvicorn order_service.main:app --reload --port 8002
Docs:  http://127.0.0.1:8002/docs

What happens when a customer clicks "Place Order":
  1. Pydantic validates the order body (address, phone, items ...)
  2. We ask the PRODUCT service for real prices (never trust prices from the browser!)
  3. We save the order with status PLACED and reply 201 immediately
  4. We drop an "OrderPlaced" message into a QUEUE
  5. The worker (workers/order_worker.py) reserves stock later -> CONFIRMED / FAILED
"""
from datetime import datetime, timezone

import httpx
from fastapi import Depends, FastAPI, HTTPException, Path, status

from common.config import settings
from common.messaging import get_queue
from order_service.schemas import COD_LIMIT, OrderCreate, OrderOut, OrderStatus, StatusUpdate

app = FastAPI(title="ShopKart Order Service", version="1.0.0")

ORDERS: dict[int, dict] = {}  # fake in-memory database


# --- [3.1] Talking to another microservice (Product Service) ---
class ProductCatalog:
    """Small HTTP client for the Product Service."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_product(self, product_id: int) -> dict | None:
        try:
            resp = httpx.get(f"{self.base_url}/products/{product_id}", timeout=3)
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product service is down, please try again",
            )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()


# --- [3.2] Dependencies (Depends) -> easy to swap in tests ---
def get_catalog() -> ProductCatalog:
    return ProductCatalog(settings.product_service_url)


def get_order_queue():
    return get_queue()


@app.get("/health", tags=["ops"])
def health():
    return {"service": "order-service", "status": "ok"}


# --- [3.3] Place an order ---
@app.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED, tags=["orders"])
def place_order(
    order: OrderCreate,
    catalog: ProductCatalog = Depends(get_catalog),
    queue=Depends(get_order_queue),
):
    lines = []
    for item in order.items:
        product = catalog.get_product(item.product_id)
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        lines.append({
            "product_id": item.product_id,
            "name": product["name"],
            "unit_price": product["price"],
            "quantity": item.quantity,
            "line_total": product["price"] * item.quantity,
        })

    total = sum(line["line_total"] for line in lines)
    if order.payment_mode == "COD" and total > COD_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cash on Delivery is allowed only up to Rs {COD_LIMIT}",
        )

    order_id = len(ORDERS) + 1
    saved = {
        "id": order_id,
        "customer_name": order.customer_name,
        "email": order.email,
        "status": OrderStatus.PLACED,
        "payment_mode": order.payment_mode,
        "lines": lines,
        "total_amount": total,
        "shipping_address": order.shipping_address.model_dump(),
        "created_at": datetime.now(timezone.utc),
        "note": "Waiting for stock confirmation",
    }
    ORDERS[order_id] = saved

    # Fire-and-forget: tell the rest of the system "an order was placed"
    queue.send({
        "event": "OrderPlaced",
        "order_id": order_id,
        "email": order.email,
        "items": [item.model_dump() for item in order.items],
        "attempt": 1,
    })
    return saved


# --- [3.4] Read orders ---
@app.get("/orders/{order_id}", response_model=OrderOut, tags=["orders"])
def get_order(order_id: int = Path(gt=0)):
    order = ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


@app.get("/orders", response_model=list[OrderOut], tags=["orders"])
def list_orders(status_filter: OrderStatus | None = None):
    orders = list(ORDERS.values())
    if status_filter:
        orders = [o for o in orders if o["status"] == status_filter]
    return orders


# --- [3.5] Change status (called by the worker) and cancel (called by customer) ---
@app.patch("/orders/{order_id}/status", response_model=OrderOut, tags=["internal"])
def update_status(update: StatusUpdate, order_id: int = Path(gt=0)):
    order = ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    order["status"] = update.status
    order["note"] = update.note
    return order


@app.post("/orders/{order_id}/cancel", response_model=OrderOut, tags=["orders"])
def cancel_order(order_id: int = Path(gt=0)):
    order = ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    if order["status"] == OrderStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="Order is already cancelled")
    order["status"] = OrderStatus.CANCELLED
    order["note"] = "Cancelled by customer"
    return order
