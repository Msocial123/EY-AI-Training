"""
Module 1.2 - YAML configuration for ShopKart.

Real life: GST %, shipping fee and coupons change often (festival sales!).
Hard-coding them means a code change + redeploy every time.
Keeping them in settings.yaml means: edit the file, restart, done.
"""
from pathlib import Path

import yaml   # pip install pyyaml

CONFIG_FILE = Path(__file__).parent / "config" / "settings.yaml"


def load_settings():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)        # ALWAYS safe_load, never yaml.load


def calculate_cart_total(cart_amount, settings, coupon_code=None):
    store = settings["store"]

    # 1. Coupon discount (only if feature flag is ON)
    discount = 0.0
    if coupon_code and settings["features"]["coupons_enabled"]:
        for coupon in settings["coupons"]:
            if coupon["code"] == coupon_code:
                discount = cart_amount * coupon["discount_percent"] / 100
    after_discount = cart_amount - discount

    # 2. GST
    gst = after_discount * store["gst_percent"] / 100

    # 3. Shipping
    shipping = 0 if after_discount >= store["free_shipping_above"] else store["shipping_fee"]

    total = after_discount + gst + shipping
    return {
        "cart": cart_amount, "discount": round(discount, 2), "gst": round(gst, 2),
        "shipping": shipping, "total": round(total, 2),
    }


if __name__ == "__main__":
    settings = load_settings()

    print("=== Settings loaded from YAML ===")
    print("App name      :", settings["app"]["name"])
    print("Environment   :", settings["app"]["environment"])
    print("GST percent   :", settings["store"]["gst_percent"])
    print("Coupons       :", [c["code"] for c in settings["coupons"]])
    print("Python type of 'debug':", type(settings["app"]["debug"]).__name__)

    print("\n=== Cart calculations driven by config ===")
    print("Small cart, no coupon   :", calculate_cart_total(500, settings))
    print("Big cart, no coupon     :", calculate_cart_total(1500, settings))
    print("Big cart + FEST20 coupon:", calculate_cart_total(1500, settings, "FEST20"))
