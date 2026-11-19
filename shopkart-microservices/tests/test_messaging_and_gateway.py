"""
tests/test_messaging_and_gateway.py  ->  Testing the queue + the gateway logic

`tmp_path` is a built-in pytest fixture: a fresh temporary folder per test.
`monkeypatch` is a built-in fixture to temporarily replace things.
"""
import pytest
from fastapi import HTTPException

from common.messaging import LocalQueue
from gateway.mini_gateway import BackendPool, pick_pool
from workers import order_worker


def test_local_queue_is_first_in_first_out(tmp_path):
    queue = LocalQueue("orders-test", db_file=str(tmp_path / "q.db"))
    queue.send({"order_id": 1})
    queue.send({"order_id": 2})
    assert queue.count() == 2
    assert [m["order_id"] for m in queue.receive(max_messages=5)] == [1, 2]
    assert queue.count() == 0  # receive() removes messages


def test_round_robin_rotates_servers():
    pool = BackendPool("test", ["http://a", "http://b"])
    first_choices = [pool.order_to_try()[0] for _ in range(4)]
    assert first_choices == ["http://a", "http://b", "http://a", "http://b"]


def test_unknown_route_gives_404():
    with pytest.raises(HTTPException) as err:
        pick_pool("payments")
    assert err.value.status_code == 404


def test_worker_marks_order_failed_when_out_of_stock(monkeypatch):
    """Fake the HTTP calls the worker makes, and record the final status."""
    calls = []

    class FakeResponse:
        def __init__(self, code, data):
            self.status_code = code
            self._data = data

        def json(self):
            return self._data

    def fake_post(url, json, timeout):
        calls.append(url)
        return FakeResponse(409, {"error": "Insufficient stock"})

    statuses = []
    monkeypatch.setattr(order_worker.httpx, "post", fake_post)
    monkeypatch.setattr(order_worker, "set_order_status", lambda oid, s, n: statuses.append(s))

    message = {"order_id": 9, "email": "a@b.com", "items": [{"product_id": 4, "quantity": 5}]}
    assert order_worker.process_order_message(message) == "FAILED"
    assert statuses == ["FAILED"]
