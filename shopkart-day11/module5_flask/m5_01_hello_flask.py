"""
Module 5.1 - Flask basics: app, routes, URL parameters, query strings, JSON.

Run:   python m5_01_hello_flask.py
Open:  http://127.0.0.1:5005/

Flask in one line: "when a request comes to THIS URL, run THIS function".
(We use port 5005 because macOS uses port 5000 for AirPlay.)
"""
from flask import Flask, jsonify, request

app = Flask(__name__)          # __name__ tells Flask where to find templates/static files
app.json.sort_keys = False

PRODUCTS = {
    101: {"id": 101, "name": "Wireless Mouse", "price": 799.0, "category": "electronics"},
    102: {"id": 102, "name": "Cotton T-Shirt", "price": 499.0, "category": "fashion"},
    104: {"id": 104, "name": "Bluetooth Earbuds", "price": 1999.0, "category": "electronics"},
}


# 1. Simplest route: returns HTML text
@app.route("/")
def home():
    return "<h1>Welcome to ShopKart</h1><p>Try /products/101 or /search?q=mouse</p>"


# 2. Dynamic URL part: <int:product_id> is converted to int automatically
@app.route("/products/<int:product_id>")
def product_page(product_id):
    product = PRODUCTS.get(product_id)
    if product is None:
        return f"<h2>Sorry, product {product_id} not found</h2>", 404
    return f"<h2>{product['name']}</h2><p>Price: Rs.{product['price']}</p>"


# 3. Query string: /search?q=mouse&max_price=1000
@app.route("/search")
def search():
    q = request.args.get("q", "").lower()
    max_price = request.args.get("max_price", type=float)        # None if not given
    results = [p for p in PRODUCTS.values() if q in p["name"].lower()]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    return jsonify(query=q, max_price=max_price, results=results)


# 4. JSON API route (what mobile apps call)
@app.route("/api/products")
def api_products():
    return jsonify(list(PRODUCTS.values()))


# 5. Same URL, different HTTP methods
@app.route("/api/newsletter", methods=["GET", "POST"])
def newsletter():
    if request.method == "POST":
        email = (request.get_json(silent=True) or {}).get("email")
        if not email:
            return jsonify(error="email is required"), 400
        return jsonify(message=f"{email} subscribed to sale alerts"), 201
    return jsonify(message="POST your email here to get sale alerts")


if __name__ == "__main__":
    # debug=True -> auto-reload when you save the file + detailed error page.
    # NEVER use debug=True in production.
    app.run(port=5005, debug=True)
