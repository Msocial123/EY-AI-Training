"""
Module 4 - ORDER microservice  (runs on port 5002)

Owns ONE thing: orders. It does NOT have its own product data.
To place an order it TALKS to the Catalog service over HTTP:
    1. GET   catalog /api/products/<id>         -> price + stock
    2. PATCH catalog /api/products/<id>/stock   -> reduce stock
    3. save the order here

If the Catalog service is down, we return 503 instead of crashing.
"""
import itertools
import logging

import requests
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s | order-service | %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.json.sort_keys = False                  # keep keys in the order we wrote them

CATALOG_URL = "http://127.0.0.1:5001"        # in real life this comes from config / env
TIMEOUT_SECONDS = 3                          # never wait forever for another service
ORDERS = {}
order_numbers = itertools.count(5001)


@app.get("/health")
def health():
    return jsonify(status="UP", service="orders")


@app.post("/api/orders")
def place_order():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    if not isinstance(product_id, int) or not isinstance(quantity, int) or quantity < 1:
        return jsonify(error="Send JSON like {\"product_id\": 101, \"quantity\": 2}"), 400

    try:
        # Step 1: ask Catalog for the product
        resp = requests.get(f"{CATALOG_URL}/api/products/{product_id}", timeout=TIMEOUT_SECONDS)
        if resp.status_code == 404:
            return jsonify(error=f"Product {product_id} does not exist"), 404
        product = resp.json()

        # Step 2: ask Catalog to reduce stock
        resp = requests.patch(f"{CATALOG_URL}/api/products/{product_id}/stock",
                              json={"change": -quantity}, timeout=TIMEOUT_SECONDS)
        if resp.status_code == 409:
            return jsonify(error="Out of stock", available=product["stock"]), 409
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Catalog service problem: %s", e)
        return jsonify(error="Catalog service unavailable, try again later"), 503

    # Step 3: save the order in OUR service
    order_id = f"ORD-{next(order_numbers)}"
    order = {"order_id": order_id, "product_id": product_id, "product_name": product["name"],
             "quantity": quantity, "total": product["price"] * quantity, "status": "PLACED"}
    ORDERS[order_id] = order
    logger.info("Placed %s: %d x %s", order_id, quantity, product["name"])
    return jsonify(order), 201


@app.get("/api/orders/<order_id>")
def get_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return jsonify(error=f"Order {order_id} not found"), 404
    return jsonify(order)


if __name__ == "__main__":
    app.run(port=5002, debug=True)
