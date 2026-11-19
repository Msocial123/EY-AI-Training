"""
Module 1.1 - JSON basics with a ShopKart product catalogue.

Real life: every API response from Amazon / Flipkart / Swiggy is JSON.
We will:
  1. Convert Python dict  <->  JSON string   (json.dumps / json.loads)
  2. Read a JSON file      (json.load)
  3. Write a JSON report   (json.dump)
  4. Handle broken JSON safely
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent          # folder of THIS file
DATA_FILE = BASE_DIR / "data" / "products.json"
OUTPUT_DIR = BASE_DIR / "output"


def dict_to_json_and_back():
    print("=== 1. Python dict  <->  JSON string ===")
    order = {"order_id": "ORD-1001", "amount": 1298.0, "paid": True, "coupon": None}

    json_text = json.dumps(order)                  # dict  -> str
    print("JSON string :", json_text)
    print("Type        :", type(json_text).__name__)

    back_to_dict = json.loads(json_text)           # str   -> dict
    print("Order amount:", back_to_dict["amount"])
    print("Pretty JSON :\n" + json.dumps(order, indent=2))


def load_products():
    print("\n=== 2. Read products.json ===")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)                    # file -> list of dicts

    print(f"Loaded {len(products)} products")
    for p in products:
        status = "IN STOCK" if p["stock"] > 0 else "OUT OF STOCK"
        print(f"  {p['id']} | {p['name']:<20} | Rs.{p['price']:>8.2f} | {status}")
    return products


def write_low_stock_report(products, threshold=5):
    print("\n=== 3. Write a low-stock report (json.dump) ===")
    low_stock = [
        {"id": p["id"], "name": p["name"], "stock": p["stock"]}
        for p in products
        if p["stock"] <= threshold
    ]
    OUTPUT_DIR.mkdir(exist_ok=True)
    report_file = OUTPUT_DIR / "low_stock_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({"threshold": threshold, "items": low_stock}, f, indent=2)
    print(f"{len(low_stock)} items need restock -> saved to {report_file.name}")


def handle_bad_json():
    print("\n=== 4. Broken JSON from a partner API ===")
    bad_response = '{"order_id": "ORD-1002", "amount": 499.0,'   # cut off!
    try:
        json.loads(bad_response)
    except json.JSONDecodeError as e:
        print(f"Could not parse response: {e.msg} (line {e.lineno}, col {e.colno})")


if __name__ == "__main__":
    dict_to_json_and_back()
    products = load_products()
    write_low_stock_report(products)
    handle_bad_json()
