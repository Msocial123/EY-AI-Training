"""
LAB 10 (bonus) - A mini ShopKart REST API that uses everything from Day 9
=========================================================================
This is how the code from labs 1-9 looks inside a REAL backend service.
The frontend team (React / mobile app) calls these endpoints.

  GET  /api/products?category=Electronics      Cosmos single-partition query
  GET  /api/products/search?q=shoe              Cosmos parameterised CONTAINS query
  GET  /api/orders/<customerId>                 Cosmos 'My Orders'
  GET  /api/products/<sku>/image                302 redirect to a 10-min read SAS (Blob)
  POST /api/vendor/upload-url  {"fileName":..}  returns a write-only SAS for ONE blob
  GET  /health                                  liveness probe

Run:   python labs/lab10_shopkart_api.py
Open:  http://127.0.0.1:5000/api/products?category=Books
"""
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask import Flask, jsonify, redirect, request  # noqa: E402
from azure.storage.blob import BlobSasPermissions, generate_blob_sas  # noqa: E402

from common.clients import blob_service_client, cosmos_database  # noqa: E402

app = Flask(__name__)
_cache = {}

CATEGORY_FOLDER = {"ELEC": "electronics", "FASH": "fashion", "HOME": "home-kitchen", "BOOK": "books", "GROC": "grocery"}


def products():
    if "products" not in _cache:                       # create clients ONCE, reuse them
        _cache["products"] = cosmos_database().get_container_client("products")
    return _cache["products"]


def orders():
    if "orders" not in _cache:
        _cache["orders"] = cosmos_database().get_container_client("orders")
    return _cache["orders"]


def blobs():
    if "blobs" not in _cache:
        _cache["blobs"] = blob_service_client()
    return _cache["blobs"]


def sas_url(container: str, blob_name: str, permission: BlobSasPermissions, minutes: int) -> str:
    svc = blobs()
    sas = generate_blob_sas(svc.account_name, container, blob_name, account_key=svc.credential.account_key,
                            permission=permission, expiry=datetime.now(timezone.utc) + timedelta(minutes=minutes))
    return f"{svc.url.rstrip('/')}/{container}/{blob_name}?{sas}"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/products")
def list_products():
    category = request.args.get("category")
    if not category:
        return {"error": "category is required (keeps the query single-partition and cheap)"}, 400
    items = list(products().query_items(
        "SELECT c.id, c.name, c.brand, c.price, c.rating, c.stock FROM c WHERE c.category = @cat ORDER BY c.price",
        parameters=[{"name": "@cat", "value": category}], partition_key=category))
    return jsonify(items)


@app.get("/api/products/search")
def search_products():
    q = (request.args.get("q") or "").strip().lower()
    if len(q) < 2:
        return {"error": "type at least 2 characters"}, 400
    items = list(products().query_items(
        "SELECT TOP 20 c.id, c.name, c.category, c.price FROM c WHERE CONTAINS(LOWER(c.name), @q)",
        parameters=[{"name": "@q", "value": q}], enable_cross_partition_query=True))
    return jsonify(items)


@app.get("/api/orders/<customer_id>")
def my_orders(customer_id):
    items = list(orders().query_items(
        "SELECT c.id, c.orderDate, c.status, c.total FROM c ORDER BY c.orderDate DESC",
        partition_key=customer_id))
    return jsonify(items)


@app.get("/api/products/<sku>/image")
def product_image(sku):
    if not re.fullmatch(r"[A-Z]{4}-\d{4}", sku):
        return {"error": "bad sku"}, 400
    blob_name = f"{CATEGORY_FOLDER.get(sku[:4], 'misc')}/{sku}.png"
    if not blobs().get_blob_client("product-images", blob_name).exists():
        return {"error": "image not found"}, 404
    return redirect(sas_url("product-images", blob_name, BlobSasPermissions(read=True), 10), code=302)


@app.post("/api/vendor/upload-url")
def vendor_upload_url():
    body = request.get_json(silent=True) or {}
    file_name = body.get("fileName", "")
    vendor = body.get("vendorId", "")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}\.(pdf|png|jpg|jpeg)", file_name) or not re.fullmatch(r"[a-z0-9-]{2,40}", vendor):
        return {"error": "invalid fileName or vendorId"}, 400
    blob_name = f"{vendor}/{file_name}"
    url = sas_url("vendor-uploads", blob_name, BlobSasPermissions(create=True, write=True), 10)
    return {"uploadUrl": url, "method": "PUT", "headers": {"x-ms-blob-type": "BlockBlob"}, "expiresInMinutes": 10}


if __name__ == "__main__":
    app.run(debug=True)
