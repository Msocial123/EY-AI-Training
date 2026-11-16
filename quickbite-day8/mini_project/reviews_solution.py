"""END-OF-DAY MINI PROJECT - QuickBite Reviews Service (TRAINER SOLUTION)"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from datetime import datetime, timezone
from azure.cosmos import exceptions
from qb.config import get_container

reviews = get_container("Reviews", "/restaurantId")
restaurants = get_container("Restaurants", "/id")


def _rid(restaurant_id, customer_id):
    return f"rev-{restaurant_id}-{customer_id}"


def add_review(restaurant_id, customer_id, rating, text):
    if not 1 <= rating <= 5:
        raise ValueError("rating must be 1..5")
    doc = {"id": _rid(restaurant_id, customer_id), "restaurantId": restaurant_id, "type": "review",
           "customerId": customer_id, "rating": rating, "text": text,
           "createdAt": datetime.now(timezone.utc).isoformat()}
    reviews.create_item(doc)                     # 409 if this customer already reviewed
    restaurants.patch_item(restaurant_id, restaurant_id, [
        {"op": "incr", "path": "/ratingCount", "value": 1},
        {"op": "incr", "path": "/ratingSum", "value": rating}])
    return doc


def latest_reviews(restaurant_id, n=3):
    return list(reviews.query_items(
        "SELECT TOP @n c.customerId, c.rating, c.text, c.createdAt FROM c ORDER BY c.createdAt DESC",
        parameters=[{"name": "@n", "value": n}], partition_key=restaurant_id))


def average_rating(restaurant_id):
    r = restaurants.read_item(restaurant_id, partition_key=restaurant_id)   # 1 RU, not a scan
    return r["ratingSum"] / r["ratingCount"] if r["ratingCount"] else 0.0


def edit_review(restaurant_id, customer_id, new_rating, new_text):
    if not 1 <= new_rating <= 5:
        raise ValueError("rating must be 1..5")
    old = reviews.read_item(_rid(restaurant_id, customer_id), partition_key=restaurant_id)
    reviews.patch_item(old["id"], restaurant_id, [
        {"op": "set", "path": "/rating", "value": new_rating},
        {"op": "set", "path": "/text", "value": new_text}])
    restaurants.patch_item(restaurant_id, restaurant_id, [
        {"op": "incr", "path": "/ratingSum", "value": new_rating - old["rating"]}])


def delete_review(restaurant_id, customer_id):
    try:
        old = reviews.read_item(_rid(restaurant_id, customer_id), partition_key=restaurant_id)
    except exceptions.CosmosResourceNotFoundError:
        return
    reviews.delete_item(old["id"], partition_key=restaurant_id)
    restaurants.patch_item(restaurant_id, restaurant_id, [
        {"op": "incr", "path": "/ratingCount", "value": -1},
        {"op": "incr", "path": "/ratingSum", "value": -old["rating"]}])

# NOTE for discussion: review + summary live in two containers, so the two writes are NOT one
# transaction. Production fix: Change Feed + Azure Function recomputes the summary (eventually consistent).
