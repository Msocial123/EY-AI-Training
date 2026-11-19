"""
tests/test_inventory_api.py  ->  Testing a FLASK app with pytest

Flask has its own test client: app.test_client()
Same idea as FastAPI's TestClient - no server needed.
"""


def test_reserve_reduces_stock(inventory_client):
    response = inventory_client.post(
        "/inventory/reserve", json={"order_id": 1, "product_id": 1, "quantity": 5}
    )
    assert response.status_code == 200
    assert response.get_json()["remaining"] == 20


def test_reserve_more_than_available_returns_409(inventory_client):
    response = inventory_client.post(
        "/inventory/reserve", json={"order_id": 1, "product_id": 4, "quantity": 5}
    )
    assert response.status_code == 409
    assert response.get_json()["available"] == 3


def test_reserve_with_bad_body_returns_400(inventory_client):
    response = inventory_client.post("/inventory/reserve", json={"product_id": "abc"})
    assert response.status_code == 400


def test_unknown_product_returns_404(inventory_client):
    assert inventory_client.get("/inventory/999").status_code == 404


def test_restock_adds_units(inventory_client):
    inventory_client.post("/inventory/restock", json={"product_id": 4, "quantity": 10})
    assert inventory_client.get("/inventory/4").get_json()["available"] == 13
