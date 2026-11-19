"""
tests/test_product_api.py  ->  API tests for the Product Service (FastAPI TestClient)

TestClient calls the app directly in memory - no uvicorn, no port needed.
Run:   pytest tests/test_product_api.py -v
"""
import pytest


def test_health(product_client):
    response = product_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ---------- Path parameters ----------
def test_get_existing_product(product_client):
    response = product_client.get("/products/1")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Apple iPhone 15 (128 GB)"
    assert body["discount_percent"] == 12


def test_get_missing_product_returns_404(product_client):
    response = product_client.get("/products/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product 999 not found"


def test_product_id_must_be_positive(product_client):
    assert product_client.get("/products/0").status_code == 422
    assert product_client.get("/products/abc").status_code == 422


# ---------- Query parameters ----------
def test_filter_by_category(product_client):
    response = product_client.get("/products", params={"category": "books"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["category"] == "books"


def test_price_range_and_sorting(product_client):
    response = product_client.get(
        "/products", params={"min_price": 500, "max_price": 3000, "sort_by": "price_asc"}
    )
    prices = [p["price"] for p in response.json()["items"]]
    assert prices == sorted(prices)
    assert all(500 <= p <= 3000 for p in prices)


@pytest.mark.parametrize(
    "params",
    [{"category": "toys"}, {"size": 100}, {"page": 0}, {"search": "a"}, {"sort_by": "random"}],
)
def test_invalid_query_params_return_422(product_client, params):
    assert product_client.get("/products", params=params).status_code == 422


def test_pagination(product_client):
    response = product_client.get("/products", params={"page": 2, "size": 2})
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2


# ---------- Request body + status codes ----------
def test_create_product_returns_201(product_client, new_product_payload):
    response = product_client.post("/products", json=new_product_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 6
    assert body["tags"] == ["audio", "earbuds"]


def test_create_duplicate_name_returns_409(product_client, new_product_payload):
    product_client.post("/products", json=new_product_payload)
    response = product_client.post("/products", json=new_product_payload)
    assert response.status_code == 409


def test_create_with_missing_seller_returns_422(product_client, new_product_payload):
    del new_product_payload["seller"]
    response = product_client.post("/products", json=new_product_payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "seller"]


def test_patch_price_for_flash_sale(product_client):
    response = product_client.patch("/products/1", json={"price": 64999})
    assert response.status_code == 200
    assert response.json()["price"] == 64999


def test_patch_cannot_break_price_rule(product_client):
    response = product_client.patch("/products/1", json={"price": 99999})  # mrp is 79900
    assert response.status_code == 422


def test_delete_then_get_returns_404(product_client):
    assert product_client.delete("/products/2").status_code == 204
    assert product_client.get("/products/2").status_code == 404


def test_every_response_has_instance_header(product_client):
    assert "x-instance" in product_client.get("/health").headers
