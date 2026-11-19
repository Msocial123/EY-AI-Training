"""
Module 4.1 - Talking to a REST API from Python with `requests`.

First start the catalog service in ANOTHER terminal:
    python catalog_service.py

Then run:   python m4_01_rest_client.py
Every call prints:  METHOD  URL  ->  STATUS CODE  + response body
"""
import json

import requests   # pip install requests

BASE_URL = "http://127.0.0.1:5001"


def show(resp):
    """Print one HTTP request/response in a readable way."""
    print(f"\n{resp.request.method:<6} {resp.url}  ->  {resp.status_code} {resp.reason}")
    if resp.text:
        body = json.dumps(resp.json(), indent=2)
        print("\n".join(body.splitlines()[:12]))     # first 12 lines is enough
    return resp


if __name__ == "__main__":
    print("=== READ: GET is safe - it never changes data ===")
    show(requests.get(f"{BASE_URL}/health", timeout=5))
    show(requests.get(f"{BASE_URL}/api/products", params={"category": "electronics"}, timeout=5))
    show(requests.get(f"{BASE_URL}/api/products/101", timeout=5))
    show(requests.get(f"{BASE_URL}/api/products/999", timeout=5))            # 404

    print("\n=== CREATE: POST adds a new resource ===")
    new_product = {"name": "Yoga Mat", "price": 899.0, "stock": 30, "category": "fitness"}
    created = show(requests.post(f"{BASE_URL}/api/products", json=new_product, timeout=5))
    new_id = created.json()["id"]
    print("Location header:", created.headers.get("Location"))
    show(requests.post(f"{BASE_URL}/api/products", json={"name": "Half data"}, timeout=5))  # 400

    print("\n=== UPDATE: PUT replaces everything, PATCH changes a part ===")
    full = {"name": "Yoga Mat Pro", "price": 1299.0, "stock": 25, "category": "fitness"}
    show(requests.put(f"{BASE_URL}/api/products/{new_id}", json=full, timeout=5))
    show(requests.patch(f"{BASE_URL}/api/products/{new_id}/stock", json={"change": -5}, timeout=5))
    show(requests.patch(f"{BASE_URL}/api/products/104/stock", json={"change": -10}, timeout=5))  # 409

    print("\n=== DELETE: remove the resource ===")
    show(requests.delete(f"{BASE_URL}/api/products/{new_id}", timeout=5))     # 204
    show(requests.get(f"{BASE_URL}/api/products/{new_id}", timeout=5))        # now 404
