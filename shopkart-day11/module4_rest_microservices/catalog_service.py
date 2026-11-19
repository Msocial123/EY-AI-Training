"""
Module 4 - CATALOG microservice  (runs on port 5001)

Owns ONE thing: products and their stock.
In Module 4 we USE this API as a black box (like a frontend developer).
In Module 5 we learn how to BUILD APIs like this in Flask.

REST design used here:
  GET    /health                      -> is the service alive?
  GET    /api/products                -> list products   (?category=electronics)
  GET    /api/products/<id>           -> one product
  POST   /api/products                -> create          -> 201 Created
  PUT    /api/products/<id>           -> replace whole product
  PATCH  /api/products/<id>/stock     -> change only stock
  DELETE /api/products/<id>           -> delete          -> 204 No Content
"""
from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.sort_keys = False                  # keep keys in the order we wrote them

PRODUCTS = {
    101: {"id": 101, "name": "Wireless Mouse", "price": 799.0, "stock": 50, "category": "electronics"},
    102: {"id": 102, "name": "Cotton T-Shirt", "price": 499.0, "stock": 120, "category": "fashion"},
    103: {"id": 103, "name": "Steel Water Bottle", "price": 349.0, "stock": 0, "category": "home"},
    104: {"id": 104, "name": "Bluetooth Earbuds", "price": 1999.0, "stock": 4, "category": "electronics"},
}
REQUIRED_FIELDS = {"name", "price", "stock", "category"}


@app.get("/health")
def health():
    return jsonify(status="UP", service="catalog")


@app.get("/api/products")
def list_products():
    category = request.args.get("category")              # query parameter
    items = list(PRODUCTS.values())
    if category:
        items = [p for p in items if p["category"] == category]
    return jsonify(count=len(items), items=items)


@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    product = PRODUCTS.get(product_id)
    if product is None:
        return jsonify(error=f"Product {product_id} not found"), 404
    return jsonify(product)


@app.post("/api/products")
def create_product():
    data = request.get_json(silent=True) or {}
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        return jsonify(error=f"Missing fields: {sorted(missing)}"), 400
    new_id = max(PRODUCTS) + 1
    product = {"id": new_id, **{k: data[k] for k in REQUIRED_FIELDS}}
    PRODUCTS[new_id] = product
    return jsonify(product), 201, {"Location": f"/api/products/{new_id}"}


@app.put("/api/products/<int:product_id>")
def replace_product(product_id):
    if product_id not in PRODUCTS:
        return jsonify(error=f"Product {product_id} not found"), 404
    data = request.get_json(silent=True) or {}
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        return jsonify(error=f"PUT needs the FULL product. Missing: {sorted(missing)}"), 400
    PRODUCTS[product_id] = {"id": product_id, **{k: data[k] for k in REQUIRED_FIELDS}}
    return jsonify(PRODUCTS[product_id])


@app.patch("/api/products/<int:product_id>/stock")
def change_stock(product_id):
    product = PRODUCTS.get(product_id)
    if product is None:
        return jsonify(error=f"Product {product_id} not found"), 404
    data = request.get_json(silent=True) or {}
    change = data.get("change")                     # e.g. -2 (sold) or +100 (restock)
    if not isinstance(change, int):
        return jsonify(error="Send JSON like {\"change\": -2}"), 400
    if product["stock"] + change < 0:
        return jsonify(error="Not enough stock", available=product["stock"]), 409
    product["stock"] += change
    return jsonify(product)


@app.delete("/api/products/<int:product_id>")
def delete_product(product_id):
    if PRODUCTS.pop(product_id, None) is None:
        return jsonify(error=f"Product {product_id} not found"), 404
    return "", 204


if __name__ == "__main__":
    app.run(port=5001, debug=True)
