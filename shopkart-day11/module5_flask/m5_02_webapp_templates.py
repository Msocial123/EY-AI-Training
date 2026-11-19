"""
Module 5.2 - A small ShopKart WEB APP with HTML templates (Jinja2) and a form.

Run:   python m5_02_webapp_templates.py
Open:  http://127.0.0.1:5005/

Pages:
  /                     -> product listing (loop + if in template)
  /product/<id>         -> product detail page
  /product/<id>/notify  -> "Notify me when back in stock" form (GET shows, POST submits)
"""
from flask import Flask, abort, redirect, render_template, request, url_for

app = Flask(__name__)

PRODUCTS = [
    {"id": 101, "name": "Wireless Mouse", "price": 799.0, "mrp": 999.0, "stock": 50},
    {"id": 102, "name": "Cotton T-Shirt", "price": 499.0, "mrp": 699.0, "stock": 120},
    {"id": 103, "name": "Steel Water Bottle", "price": 349.0, "mrp": 499.0, "stock": 0},
    {"id": 104, "name": "Bluetooth Earbuds", "price": 1999.0, "mrp": 3499.0, "stock": 4},
]
NOTIFY_REQUESTS = []        # in real life: a database table


def find_product(product_id):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    abort(404)              # stops here and shows the 404 page


@app.route("/")
def index():
    return render_template("index.html", products=PRODUCTS, title="All Products")


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = find_product(product_id)
    return render_template("product.html", product=product, title=product["name"])


@app.route("/product/<int:product_id>/notify", methods=["GET", "POST"])
def notify_me(product_id):
    product = find_product(product_id)
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()      # form fields -> request.form
        if "@" not in email:
            error = "Please enter a valid email"
        else:
            NOTIFY_REQUESTS.append({"product_id": product_id, "email": email})
            # Post/Redirect/Get pattern: refresh will not submit the form twice
            return redirect(url_for("product_detail", product_id=product_id, subscribed=1))
    return render_template("notify.html", product=product, error=error, title="Notify me")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", title="Not found"), 404


if __name__ == "__main__":
    app.run(port=5005, debug=True)
