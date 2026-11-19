"""
inventory_service/app.py   ->   ShopKart INVENTORY microservice (Flask)

Run:   python -m inventory_service.app        (port 8003)
   or  flask --app inventory_service.app run --port 8003

Why Flask here?  In real companies you WILL find both. Many older services are
Flask, newer ones are FastAPI. A microservice architecture lets them live
together - they only talk over HTTP + JSON.

Notice how much MORE code we write in Flask for validation and errors,
compared to FastAPI which does it automatically.
"""
from flask import Flask, jsonify, request
from pydantic import BaseModel, Field, ValidationError

app = Flask(__name__)

# product_id -> units available in the warehouse
STOCK: dict[int, int] = {}


def reset_stock() -> None:
    STOCK.clear()
    STOCK.update({1: 25, 2: 40, 3: 100, 4: 3, 5: 15})  # Atomic Habits has only 3 left!


reset_stock()


# --- [3.6] Pydantic models used inside Flask ---
class ReserveRequest(BaseModel):
    order_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=10)


class RestockRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=1000)


# --- [3.7] Routes ---
@app.get("/health")
def health():
    return jsonify(service="inventory-service", status="ok")


@app.get("/inventory")
def all_stock():
    return jsonify([{"product_id": pid, "available": qty} for pid, qty in STOCK.items()])


@app.get("/inventory/<int:product_id>")
def stock_for_product(product_id: int):
    if product_id not in STOCK:
        return jsonify(error=f"Product {product_id} not tracked"), 404
    return jsonify(product_id=product_id, available=STOCK[product_id])


@app.post("/inventory/reserve")
def reserve_stock():
    """Called by the order worker: 'hold 2 units of product 1 for order 7'."""
    try:
        data = ReserveRequest(**(request.get_json(silent=True) or {}))
    except ValidationError as err:
        return jsonify(error="Invalid request", details=err.errors(include_url=False, include_context=False)), 400

    available = STOCK.get(data.product_id)
    if available is None:
        return jsonify(error=f"Product {data.product_id} not tracked"), 404
    if available < data.quantity:
        return jsonify(
            error="Insufficient stock", product_id=data.product_id, available=available
        ), 409

    STOCK[data.product_id] = available - data.quantity
    return jsonify(
        message="Reserved", order_id=data.order_id,
        product_id=data.product_id, remaining=STOCK[data.product_id],
    ), 200


@app.post("/inventory/restock")
def restock():
    """Warehouse team adds new units."""
    try:
        data = RestockRequest(**(request.get_json(silent=True) or {}))
    except ValidationError as err:
        return jsonify(error="Invalid request", details=err.errors(include_url=False, include_context=False)), 400
    STOCK[data.product_id] = STOCK.get(data.product_id, 0) + data.quantity
    return jsonify(product_id=data.product_id, available=STOCK[data.product_id]), 200


if __name__ == "__main__":
    app.run(port=8003, debug=True)
