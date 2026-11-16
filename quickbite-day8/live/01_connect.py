"""LIVE 1 - Connect to Cosmos DB and save the first QuickBite order   (Module 8.1)"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import json
from qb.config import get_client, get_container, ru, title

title("LIVE 1 - Hello Cosmos DB")

# STEP 1: the account. SAY: "One client per app. It's thread-safe - create it once, reuse it."
client = get_client()
acct = client.get_database_account()
print("Write regions:", [l["name"] for l in acct.WritableLocations])
print("Read regions :", [l["name"] for l in acct.ReadableLocations])
print("Default consistency:", (acct.ConsistencyPolicy or {}).get("defaultConsistencyLevel"))

# STEP 2: database + container. SAY: "Container = unit of scale. Partition key is chosen NOW, forever."
orders = get_container("Orders", "/customerId", client=client)

# STEP 3: one JSON document. SAY: "No CREATE TABLE. No schema. The JSON IS the row."
order = {
    "id": "ord-0001",
    "customerId": "cust-001",          # partition key value
    "restaurantName": "Paradise Biryani House",
    "status": "PLACED",
    "items": [{"item": "Chicken Dum Biryani", "qty": 2, "price": 320}],
    "total": 640,
}
orders.upsert_item(order)
print(f"\nSaved ord-0001  ({ru(orders):.2f} RU)")

# STEP 4: read it back. SAY: "id + partition key = the cheapest operation in Cosmos DB."
saved = orders.read_item("ord-0001", partition_key="cust-001")
print(f"Read back ({ru(orders):.2f} RU):")
print(json.dumps(saved, indent=2))
print("\nNotice _rid, _ts, _etag, _self -> added by Cosmos DB, not by us.")
