"""
Offline smoke tests - run every lab's Python logic WITHOUT Azure.

Cosmos DB is replaced by a tiny in-memory fake, so you can check that the code
runs end-to-end on any laptop (useful in CI / GitHub Actions too).

    python -m pytest tests -q        (or)        python tests/test_labs_offline.py

Blob labs (7, 8) need Azurite running:  azurite-blob --location ./.azurite
"""
import copy
import importlib
import json
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "labs"))
os.environ.setdefault("COSMOS_KEY", "offline-test-key")
os.environ["VISION_KEY"] = ""          # force OFFLINE mode for AI labs
os.environ["DOCINTEL_KEY"] = ""

from azure.cosmos import exceptions  # noqa: E402


class FakePager:
    def __init__(self, docs):
        self.docs, self.continuation_token = docs, "fake-token-abc123"

    def __next__(self):
        return iter(self.docs[:5])


class FakeQueryResult(list):
    def by_page(self):
        return FakePager(list(self))


class FakeConnection:
    last_response_headers = {"x-ms-request-charge": "2.85", "x-ms-session-token": "0:-1#7"}


class FakeContainer:
    def __init__(self, docs):
        self.docs = {d["id"]: copy.deepcopy(d) for d in docs}
        self.client_connection = FakeConnection()

    def read(self):
        return {}

    def upsert_item(self, doc, **kw):
        doc = copy.deepcopy(doc)
        doc["_etag"] = f"etag-{len(self.docs)}-{id(doc)}"
        self.docs[doc["id"]] = doc
        return doc

    def create_item(self, doc, response_hook=None, **kw):
        out = self.upsert_item(doc)
        if response_hook:
            response_hook({"x-ms-session-token": "0:-1#8"}, out)
        return out

    def read_item(self, item, partition_key, **kw):
        doc = self.docs.get(item)
        if not doc or partition_key not in (doc.get("category"), doc.get("customerId"), doc.get("vendorName")):
            raise exceptions.CosmosResourceNotFoundError(message="not found")
        return {**copy.deepcopy(doc), "_rid": "abc==", "_etag": doc.get("_etag", "etag-0"), "_ts": 1763300000}

    def replace_item(self, item, body, etag=None, match_condition=None, **kw):
        current = self.docs[item].get("_etag", "etag-0")
        if etag and etag != current:
            raise exceptions.CosmosAccessConditionFailedError(message="412")
        return self.upsert_item(body)

    def patch_item(self, item, partition_key, patch_operations, **kw):
        doc = self.docs[item]
        for op in patch_operations:
            key = op["path"].strip("/")
            doc[key] = doc.get(key, 0) + op["value"] if op["op"] == "incr" else op["value"]
        return copy.deepcopy(doc)

    def delete_item(self, item, partition_key, **kw):
        self.docs.pop(item, None)

    def query_items(self, query, parameters=None, **kw):
        q = " ".join(query.split())
        if "VALUE COUNT" in q:
            return FakeQueryResult([len(self.docs)])
        if "DISTINCT VALUE c.category" in q:
            return FakeQueryResult(sorted({d["category"] for d in self.docs.values()}))
        if "VALUE AVG" in q:
            return FakeQueryResult([1234.5])
        if "GROUP BY c.category" in q:
            return FakeQueryResult([{"category": kw.get("partition_key"), "products": 4, "avgPrice": 999.5}])
        if "GROUP BY c.status" in q:
            return FakeQueryResult([{"status": "Delivered", "n": 2}])
        return FakeQueryResult(copy.deepcopy(list(self.docs.values())))


class FakeDatabase:
    def __init__(self):
        load = lambda f: json.loads((ROOT / "data" / f).read_text())  # noqa: E731
        self.containers = {"products": FakeContainer(load("products.json")),
                           "orders": FakeContainer(load("orders.json")),
                           "invoices": FakeContainer([])}
        self.id = "shopkart"

    def get_container_client(self, name):
        return self.containers[name]

    def create_container_if_not_exists(self, id, **kw):
        return self.containers[id]


DB = FakeDatabase()


class FakeAccount:
    ConsistencyPolicy = {"defaultConsistencyLevel": "Session"}


class FakeClient:
    def create_database_if_not_exists(self, id):
        return DB

    def get_database_client(self, name):
        return DB

    def get_database_account(self):
        return FakeAccount()


def patch_cosmos():
    import common.clients as clients
    clients.cosmos_client = lambda *a, **k: FakeClient()
    clients.cosmos_database = lambda client=None: DB


def run_lab(name):
    patch_cosmos()
    module = importlib.import_module(name)
    for attr in ("cosmos_client", "cosmos_database"):
        if hasattr(module, attr):
            setattr(module, attr, getattr(sys.modules["common.clients"], attr))
    module.main()


def azurite_running():
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", 10000)) == 0


def test_lab01():
    run_lab("lab01_cosmos_setup")


def test_lab02():
    run_lab("lab02_cosmos_sql_queries")


def test_lab03():
    run_lab("lab03_consistency_levels")


def test_lab04():
    run_lab("lab04_cosmos_security")


def test_lab05():
    run_lab("lab05_ocr_read")


def test_lab06():
    run_lab("lab06_document_intelligence")


def test_lab07_08_09_need_azurite():
    if not azurite_running():
        print("Azurite not running - skipping blob labs")
        return
    run_lab("lab07_blob_storage_sdk")
    run_lab("lab08_sas_links")
    run_lab("lab09_capstone_invoice_pipeline")


if __name__ == "__main__":
    for t in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        print(f"\n######## {t.__name__} ########")
        t()
    print("\nALL OFFLINE TESTS PASSED")
