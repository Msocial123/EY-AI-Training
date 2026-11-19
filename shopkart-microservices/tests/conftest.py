"""
tests/conftest.py
-----------------
pytest automatically loads this file. Fixtures defined here can be used by
ANY test just by writing their name as a function argument.

Key idea: our tests must NOT need other services running, and must NOT touch
Azure. So we replace (fake) the Product Service and the Queue.
"""
import pytest
from fastapi.testclient import TestClient

from inventory_service.app import app as inventory_app
from inventory_service.app import reset_stock
from order_service import main as order_main
from product_service import database as product_db
from product_service.main import app as product_app


# --- [4.1] Fixtures for the Product Service ---
@pytest.fixture
def product_client():
    product_db.reset_db()  # every test starts with the same 5 products
    return TestClient(product_app)


@pytest.fixture
def new_product_payload():
    return {
        "name": "boAt Airdopes 141",
        "category": "electronics",
        "price": 1099,
        "mrp": 4490,
        "tags": ["Audio", "earbuds", "audio"],
        "seller": {"name": "boAt Store", "city": "Delhi", "rating": 4.2},
    }


# --- [4.2] Fakes for the Order Service (no network, no Azure) ---
class FakeCatalog:
    PRODUCTS = {
        1: {"id": 1, "name": "Apple iPhone 15 (128 GB)", "price": 69999},
        4: {"id": 4, "name": "Atomic Habits", "price": 399},
    }

    def get_product(self, product_id: int):
        return self.PRODUCTS.get(product_id)


class FakeQueue:
    def __init__(self):
        self.sent = []

    def send(self, message: dict):
        self.sent.append(message)


@pytest.fixture
def fake_queue():
    return FakeQueue()


@pytest.fixture
def order_client(fake_queue):
    order_main.ORDERS.clear()
    order_main.app.dependency_overrides[order_main.get_catalog] = lambda: FakeCatalog()
    order_main.app.dependency_overrides[order_main.get_order_queue] = lambda: fake_queue
    yield TestClient(order_main.app)
    order_main.app.dependency_overrides.clear()  # clean up after the test


@pytest.fixture
def valid_order():
    return {
        "customer_name": "Ravi Kumar",
        "email": "ravi@example.com",
        "phone": "9876543210",
        "items": [{"product_id": 4, "quantity": 2}],
        "shipping_address": {
            "line1": "Flat 302, Sai Residency",
            "city": "Kadapa",
            "state": "Andhra Pradesh",
            "pincode": "516003",
        },
        "payment_mode": "UPI",
    }


# --- [4.3] Fixture for the Flask Inventory Service ---
@pytest.fixture
def inventory_client():
    reset_stock()
    inventory_app.config["TESTING"] = True
    return inventory_app.test_client()
