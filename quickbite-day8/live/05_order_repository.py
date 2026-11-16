"""LIVE 5 - QuickBite OrderRepository: production-style CRUD   (Module 8.6)
This is how real teams wrap Cosmos DB: one class, clear methods, errors translated
into business meaning. Build it method-by-method in front of the class."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import uuid
from datetime import datetime, timezone
from azure.core import MatchConditions
from azure.cosmos import exceptions
from qb.config import get_container, ru

# Allowed status changes - business rules live in code, not in the database
TRANSITIONS = {
    "PLACED": {"ACCEPTED", "CANCELLED"},
    "ACCEPTED": {"PREPARING", "CANCELLED"},
    "PREPARING": {"OUT_FOR_DELIVERY"},
    "OUT_FOR_DELIVERY": {"DELIVERED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}


class OrderNotFound(Exception): pass
class InvalidTransition(Exception): pass
class ConcurrentUpdate(Exception): pass


def now():
    return datetime.now(timezone.utc).isoformat()


class OrderRepository:
    def __init__(self, container=None):
        self.c = container or get_container("Orders", "/customerId")

    # ---------------- CREATE
    def place_order(self, customer_id, restaurant, items):
        if not items:
            raise ValueError("an order needs at least one item")
        order = {
            "id": f"ord-{uuid.uuid4().hex[:10]}",        # app generates ids; never trust the client
            "type": "order",
            "customerId": customer_id,
            "restaurantId": restaurant["id"],
            "restaurantName": restaurant["name"],        # denormalised: shown on every order card
            "status": "PLACED",
            "items": items,
            "total": sum(i["qty"] * i["price"] for i in items),
            "placedAt": now(),
            "history": [{"status": "PLACED", "at": now()}],
        }
        return self.c.create_item(order)                  # create (not upsert): a duplicate id is a bug

    # ---------------- READ
    def get(self, customer_id, order_id):
        try:
            return self.c.read_item(order_id, partition_key=customer_id)
        except exceptions.CosmosResourceNotFoundError:
            raise OrderNotFound(order_id)

    def my_orders(self, customer_id, page_size=5, token=None):
        """One page of a customer's orders, newest first. Returns (orders, next_token)."""
        pages = self.c.query_items(
            "SELECT c.id, c.restaurantName, c.status, c.total, c.placedAt FROM c "
            "WHERE c.type = 'order' ORDER BY c.placedAt DESC",
            partition_key=customer_id, max_item_count=page_size).by_page(token)
        page = list(next(pages, []))
        return page, pages.continuation_token

    # ---------------- UPDATE
    def update_status(self, customer_id, order_id, new_status):
        order = self.get(customer_id, order_id)
        if new_status not in TRANSITIONS[order["status"]]:
            raise InvalidTransition(f"{order['status']} -> {new_status} not allowed")
        try:
            return self.c.patch_item(order_id, customer_id, patch_operations=[
                {"op": "set", "path": "/status", "value": new_status},
                {"op": "add", "path": "/history/-", "value": {"status": new_status, "at": now()}},
            ], etag=order["_etag"], match_condition=MatchConditions.IfNotModified)
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 412:
                raise ConcurrentUpdate(order_id)        # someone changed it between our read and write
            raise

    def cancel_if_not_accepted(self, customer_id, order_id):
        """Atomic conditional patch: server only applies it if status is still PLACED."""
        try:
            return self.c.patch_item(order_id, customer_id,
                                     patch_operations=[{"op": "set", "path": "/status", "value": "CANCELLED"},
                                                       {"op": "add", "path": "/history/-",
                                                        "value": {"status": "CANCELLED", "at": now()}}],
                                     filter_predicate="FROM c WHERE c.status = 'PLACED'")
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 412:
                raise InvalidTransition("too late to cancel - restaurant already accepted")
            raise

    # ---------------- DELETE
    def delete(self, customer_id, order_id):
        try:
            self.c.delete_item(order_id, partition_key=customer_id)
        except exceptions.CosmosResourceNotFoundError:
            pass                                          # idempotent delete: already gone is fine

    def last_ru(self):
        return ru(self.c)
