"""
product_service/database.py
---------------------------
A FAKE database (a Python dict in memory) so the class can focus on APIs.
In a real project this would be Azure SQL / Cosmos DB (you saw Cosmos on Day 8).

Data is reset every time the service restarts.
"""
from datetime import datetime, timezone

SEED_PRODUCTS = [
    {
        "name": "Apple iPhone 15 (128 GB)",
        "description": "A16 Bionic chip, 48MP camera",
        "category": "electronics",
        "price": 69999,
        "mrp": 79900,
        "tags": ["apple", "mobile", "5g"],
        "seller": {"name": "RetailNet", "city": "Bengaluru", "rating": 4.6},
    },
    {
        "name": "Nike Revolution 6 Running Shoes",
        "description": "Lightweight running shoes",
        "category": "fashion",
        "price": 2797,
        "mrp": 3695,
        "tags": ["nike", "shoes", "sports"],
        "seller": {"name": "SportsHub", "city": "Mumbai", "rating": 4.3},
    },
    {
        "name": "India Gate Basmati Rice 5kg",
        "description": "Long grain basmati rice",
        "category": "grocery",
        "price": 649,
        "mrp": 850,
        "tags": ["rice", "staples"],
        "seller": {"name": "FreshMart", "city": "Hyderabad", "rating": 4.1},
    },
    {
        "name": "Atomic Habits by James Clear",
        "description": "Paperback",
        "category": "books",
        "price": 399,
        "mrp": 799,
        "tags": ["self-help", "bestseller"],
        "seller": {"name": "BookBazaar", "city": "Chennai", "rating": 4.8},
    },
    {
        "name": "Prestige Pressure Cooker 5L",
        "description": "Aluminium, induction base",
        "category": "home",
        "price": 1899,
        "mrp": 2650,
        "tags": ["kitchen", "cookware"],
        "seller": {"name": "HomeNeeds", "city": "Kadapa", "rating": 4.4},
    },
]

# product_id -> product dict
PRODUCTS: dict[int, dict] = {}
_next_id = 1


def reset_db() -> None:
    """Start fresh with the 5 seed products (used at startup and in tests)."""
    global _next_id
    PRODUCTS.clear()
    _next_id = 1
    for item in SEED_PRODUCTS:
        add_product(dict(item))


def add_product(data: dict) -> dict:
    global _next_id
    product = {"id": _next_id, "created_at": datetime.now(timezone.utc), **data}
    PRODUCTS[_next_id] = product
    _next_id += 1
    return product


reset_db()
