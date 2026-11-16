"""Deterministic QuickBite sample data (same every run)."""
import random
from datetime import datetime, timedelta, timezone

CITIES = ["Hyderabad", "Bengaluru", "Pune", "Chennai", "Kochi"]

RESTAURANTS = [
    {"id": "r-101", "name": "Paradise Biryani House", "city": "Hyderabad", "cuisine": "Biryani"},
    {"id": "r-102", "name": "Meghana Spice Kitchen", "city": "Bengaluru", "cuisine": "Andhra"},
    {"id": "r-103", "name": "Vaishali Cafe", "city": "Pune", "cuisine": "South Indian"},
    {"id": "r-104", "name": "Murugan Tiffins", "city": "Chennai", "cuisine": "South Indian"},
    {"id": "r-105", "name": "Kayees Kitchen", "city": "Kochi", "cuisine": "Kerala"},
]

MENU = {
    "r-101": [("Chicken Dum Biryani", 320), ("Veg Biryani", 240), ("Double Ka Meetha", 120)],
    "r-102": [("Andhra Meals", 260), ("Chilli Paneer", 220), ("Gongura Rice", 180)],
    "r-103": [("Masala Dosa", 110), ("Idli Vada", 90), ("Filter Coffee", 40)],
    "r-104": [("Ghee Pongal", 120), ("Mini Tiffin", 150), ("Rava Kesari", 70)],
    "r-105": [("Appam Stew", 180), ("Kerala Parotta", 60), ("Fish Moilee", 340)],
}

STATUSES = ["PLACED", "ACCEPTED", "PREPARING", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]


def customers(n=25):
    return [{"id": f"cust-{i:03d}", "name": f"Customer {i}", "city": CITIES[i % len(CITIES)]} for i in range(1, n + 1)]


def orders(n=120, seed=42):
    rnd = random.Random(seed)
    base = datetime(2026, 11, 1, tzinfo=timezone.utc)
    cs = customers()
    out = []
    for i in range(n):
        c = rnd.choice(cs)
        r = rnd.choice(RESTAURANTS)
        lines = [{"item": name, "qty": rnd.randint(1, 3), "price": price}
                 for name, price in rnd.sample(MENU[r["id"]], rnd.randint(1, 3))]
        out.append({
            "id": f"ord-{5001 + i}",
            "type": "order",
            "customerId": c["id"],
            "customerName": c["name"],
            "restaurantId": r["id"],
            "restaurantName": r["name"],
            "city": r["city"],
            "status": rnd.choice(STATUSES),
            "items": lines,
            "total": sum(l["qty"] * l["price"] for l in lines),
            "placedAt": (base + timedelta(minutes=rnd.randint(0, 60 * 24 * 14))).isoformat(),
        })
    return out
