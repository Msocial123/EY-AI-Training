"""
Module 4.2 - Two microservices working together.

Start BOTH services, each in its own terminal:
    Terminal 1:  python catalog_service.py     (port 5001)
    Terminal 2:  python order_service.py       (port 5002)
Then:
    Terminal 3:  python m4_02_microservices_demo.py

Watch: the ORDER service changes stock inside the CATALOG service.
Then stop the catalog (Ctrl+C in Terminal 1) and run this again -> 503.
"""
import requests

CATALOG = "http://127.0.0.1:5001"
ORDERS = "http://127.0.0.1:5002"


def stock_of(product_id):
    return requests.get(f"{CATALOG}/api/products/{product_id}", timeout=5).json()["stock"]


def place(product_id, quantity):
    resp = requests.post(f"{ORDERS}/api/orders",
                         json={"product_id": product_id, "quantity": quantity}, timeout=10)
    print(f"POST /api/orders {product_id} x{quantity} -> {resp.status_code}: {resp.json()}")
    return resp


if __name__ == "__main__":
    print("=== Health checks ===")
    for name, url in [("catalog", CATALOG), ("orders", ORDERS)]:
        try:
            print(name, "->", requests.get(f"{url}/health", timeout=2).json())
        except requests.exceptions.ConnectionError:
            print(name, "-> DOWN")

    print("\n=== Place orders through the ORDER service ===")
    try:
        before = stock_of(101)
        print("Mouse stock BEFORE:", before)
    except requests.exceptions.ConnectionError:
        print("Catalog is DOWN - let's see how the order service reacts:")
        place(101, 2)
        raise SystemExit

    resp = place(101, 2)           # works
    place(104, 50)                 # 409 - not enough earbuds
    place(999, 1)                  # 404 - no such product
    print("Mouse stock AFTER :", stock_of(101))

    order_id = resp.json()["order_id"]
    print("\nTrack order:", requests.get(f"{ORDERS}/api/orders/{order_id}", timeout=5).json())
