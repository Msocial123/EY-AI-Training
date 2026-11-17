"""
LAB 1 - Create the ShopKart database in Cosmos DB and load data
================================================================
Curriculum topic : "Using Azure Portal for Cosmos DB" (the SDK way of doing
                   exactly what you click in Portal -> Data Explorer)

Business story   : ShopKart is an Indian e-commerce startup. Every product has
                   different attributes (a phone has RAM, a saree has fabric,
                   a book has an author). A fixed SQL table would need 200
                   mostly-empty columns. Cosmos DB stores each product as a
                   JSON document, so every product can have its own shape.

What this script does (same as the Portal clicks in brackets):
  1. Create database 'shopkart'                 [Data Explorer > New Database]
  2. Create container 'products'  pk=/category  [New Container]
  3. Create container 'orders'    pk=/customerId
  4. Create container 'invoices'  pk=/vendorName (used in the capstone)
  5. Upsert 20 products and 15 orders           [Items > Upload Item]
  6. Read one item back by id + partition key   [click an item]

Run:  python labs/lab01_cosmos_setup.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from azure.cosmos import PartitionKey, exceptions  # noqa: E402

from common import config  # noqa: E402
from common.clients import cosmos_client, last_request_charge  # noqa: E402
from common.pretty import banner, step, ok, info, warn, show_json  # noqa: E402

CONTAINERS = {
    # container name : partition key path
    "products": "/category",     # queries are mostly "show me Electronics..."
    "orders": "/customerId",     # queries are mostly "show MY orders"
    "invoices": "/vendorName",   # finance asks "all invoices from TechNova"
}


def create_database_and_containers(client):
    step(f"Creating database '{config.COSMOS_DATABASE}' (if it does not exist)")
    db = client.create_database_if_not_exists(id=config.COSMOS_DATABASE)
    ok(f"database ready: {db.id}")

    for name, pk in CONTAINERS.items():
        step(f"Creating container '{name}' with partition key '{pk}'")
        kwargs = {"id": name, "partition_key": PartitionKey(path=pk)}
        if not config.IS_COSMOS_EMULATOR:
            kwargs["offer_throughput"] = 400  # 400 RU/s = smallest manual throughput
        try:
            db.create_container_if_not_exists(**kwargs)
        except exceptions.CosmosHttpResponseError as e:
            # Serverless and shared-throughput accounts reject a container-level RU value
            if "offer_throughput" in kwargs and e.status_code == 400:
                kwargs.pop("offer_throughput")
                db.create_container_if_not_exists(**kwargs)
            else:
                raise
        ok(f"container ready: {name}")
    return db


def load_json(file_name):
    return json.loads((config.DATA_DIR / file_name).read_text(encoding="utf-8"))


def upsert_all(container, docs, label):
    step(f"Upserting {len(docs)} {label} (insert if new, replace if exists)")
    for doc in docs:
        container.upsert_item(doc)
    ok(f"{len(docs)} {label} written. Last write cost: {last_request_charge(container)}")


def main():
    banner("LAB 1 - ShopKart Cosmos DB setup")
    info(f"Endpoint: {config.COSMOS_ENDPOINT}  (emulator={config.IS_COSMOS_EMULATOR})")

    client = cosmos_client()
    db = create_database_and_containers(client)

    products = db.get_container_client("products")
    orders = db.get_container_client("orders")
    upsert_all(products, load_json("products.json"), "products")
    upsert_all(orders, load_json("orders.json"), "orders")

    step("Point read: the CHEAPEST way to fetch one item (id + partition key)")
    item = products.read_item(item="ELEC-1001", partition_key="Electronics")
    info(f"Cost: {last_request_charge(products)}  (a 1 KB point read is ~1 RU on Azure)")
    show_json({k: item[k] for k in ("id", "name", "category", "price", "stock", "variants")})

    step("Notice the system properties Cosmos DB added automatically:")
    for prop in ("_rid", "_etag", "_ts"):
        info(f"{prop:6} = {item.get(prop)}")
    warn("_etag changes on every update -> used for optimistic concurrency (see lab02).")

    step("Wrong partition key = item NOT found (very common beginner mistake)")
    try:
        products.read_item(item="ELEC-1001", partition_key="Fashion")
    except exceptions.CosmosResourceNotFoundError:
        ok("404 Not Found, as expected. id alone is not enough - you need id + partition key.")

    banner("LAB 1 complete. Open Data Explorer to see the same data visually.")
    info("Emulator: http://localhost:1234   |   Azure: Portal > your account > Data Explorer")


if __name__ == "__main__":
    main()
