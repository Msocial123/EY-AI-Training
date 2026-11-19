"""
tests/test_order_api.py  ->  Order Service tests using FAKES (dependency overrides)

The real order service calls the Product Service over HTTP and sends a queue
message. In tests we swap both with fakes (see conftest.py), so the test is
fast, works offline and never sends a real message to Azure.
"""


def test_place_order_calculates_total(order_client, valid_order):
    response = order_client.post("/orders", json=valid_order)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PLACED"
    assert body["total_amount"] == 399 * 2


def test_place_order_sends_queue_message(order_client, valid_order, fake_queue):
    order_client.post("/orders", json=valid_order)
    assert len(fake_queue.sent) == 1
    message = fake_queue.sent[0]
    assert message["event"] == "OrderPlaced"
    assert message["items"] == [{"product_id": 4, "quantity": 2}]


def test_unknown_product_returns_404_and_sends_nothing(order_client, valid_order, fake_queue):
    valid_order["items"] = [{"product_id": 77, "quantity": 1}]
    response = order_client.post("/orders", json=valid_order)
    assert response.status_code == 404
    assert fake_queue.sent == []


def test_cod_above_limit_is_rejected(order_client, valid_order):
    valid_order["items"] = [{"product_id": 1, "quantity": 1}]  # iPhone = 69,999
    valid_order["payment_mode"] = "COD"
    response = order_client.post("/orders", json=valid_order)
    assert response.status_code == 400
    assert "Cash on Delivery" in response.json()["detail"]


def test_invalid_phone_returns_422(order_client, valid_order):
    valid_order["phone"] = "12345"
    assert order_client.post("/orders", json=valid_order).status_code == 422


def test_cancel_twice_returns_409(order_client, valid_order):
    order_id = order_client.post("/orders", json=valid_order).json()["id"]
    assert order_client.post(f"/orders/{order_id}/cancel").status_code == 200
    assert order_client.post(f"/orders/{order_id}/cancel").status_code == 409


def test_worker_status_update(order_client, valid_order):
    order_id = order_client.post("/orders", json=valid_order).json()["id"]
    response = order_client.patch(
        f"/orders/{order_id}/status", json={"status": "CONFIRMED", "note": "ok"}
    )
    assert response.json()["status"] == "CONFIRMED"
