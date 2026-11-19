"""
LAB 4 SOLUTION - REST API with Flask (uses the Lab 2 model)

Build a Reviews API on port 5006:
  GET  /api/products/<id>/reviews    -> list reviews + average rating   (404 if no product)
  POST /api/products/<id>/reviews    -> add review, 201  (422 if invalid, 404 if no product)

Test:
  curl http://127.0.0.1:5006/api/products/101/reviews
  curl -X POST http://127.0.0.1:5006/api/products/101/reviews \
       -H "Content-Type: application/json" \
       -d '{"customer_name": "Asha", "rating": 4, "comment": "Works well with my laptop"}'
"""
from flask import Flask, jsonify, request
from pydantic import ValidationError

from lab2_reviews_solution import ProductReview     # reuse the model from Lab 2

app = Flask(__name__)
app.json.sort_keys = False

PRODUCT_IDS = {101, 102, 104}
REVIEWS = {101: [], 102: [], 104: []}


@app.get("/api/products/<int:product_id>/reviews")
def list_reviews(product_id):
    if product_id not in PRODUCT_IDS:
        return jsonify(error=f"Product {product_id} not found"), 404
    reviews = REVIEWS[product_id]
    average = round(sum(r["rating"] for r in reviews) / len(reviews), 1) if reviews else None
    return jsonify(product_id=product_id, count=len(reviews), average_rating=average,
                   reviews=reviews)


@app.post("/api/products/<int:product_id>/reviews")
def add_review(product_id):
    if product_id not in PRODUCT_IDS:
        return jsonify(error=f"Product {product_id} not found"), 404
    data = request.get_json(silent=True) or {}
    data["product_id"] = product_id                 # id comes from the URL, not the body
    try:
        review = ProductReview.model_validate(data)
    except ValidationError as e:
        return jsonify(error="validation_failed",
                       details=[err["msg"] for err in e.errors()]), 422
    REVIEWS[product_id].append(review.model_dump())
    return jsonify(review.model_dump()), 201


if __name__ == "__main__":
    app.run(port=5006, debug=True)
