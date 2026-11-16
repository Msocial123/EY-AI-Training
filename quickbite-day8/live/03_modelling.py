"""LIVE 3 - Model the SAME data two ways and measure   (Module 8.4)"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from qb.config import get_container, ru, query, title

title("LIVE 3 - Embed vs Reference")
c = get_container("ModelLab", "/orderId")
lines = [{"item": "Masala Dosa", "qty": 2, "price": 110},
         {"item": "Filter Coffee", "qty": 2, "price": 40},
         {"item": "Idli Vada", "qty": 1, "price": 90}]

# Model A - EMBEDDED. SAY: "Lines are always shown with the order, a handful per order -> embed."
c.upsert_item({"id": "A-1", "orderId": "A-1", "type": "order", "items": lines,
               "total": sum(l["qty"] * l["price"] for l in lines)})

# Model B - REFERENCED (the 'SQL habit'). One header + one doc per line.
c.upsert_item({"id": "B-1", "orderId": "B-1", "type": "orderHeader"})
for n, l in enumerate(lines, 1):
    c.upsert_item({"id": f"B-1-L{n}", "orderId": "B-1", "type": "orderLine", **l})

c.read_item("A-1", partition_key="A-1"); a = ru(c)
docs, b = query(c, "SELECT * FROM c WHERE c.orderId = 'B-1'", pk="B-1")
print(f"Embedded   : 1 point read           -> {a:.2f} RU")
print(f"Referenced : query, {len(docs)} documents   -> {b:.2f} RU")
print("Writes: embedded = 1 write; referenced = 4 writes (and no JOIN to save you).")

# The counter-case. SAY: "Reviews are UNBOUNDED - a famous restaurant gets 50,000. Never embed."
print("\nRule: embed bounded + read-together data; reference unbounded / independently-changing data.")
print("Item size limit is 2 MB - an ever-growing array WILL hit it.")
