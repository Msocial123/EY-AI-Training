"""LIVE 6 - Run a real order lifecycle through the repository   (Module 8.6)"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import importlib
from qb.config import title
from qb.seed_data import RESTAURANTS, MENU

repo_mod = importlib.import_module("05_order_repository")
OrderRepository, InvalidTransition = repo_mod.OrderRepository, repo_mod.InvalidTransition

title("LIVE 6 - Order lifecycle")
repo = OrderRepository()
rest = RESTAURANTS[0]
items = [{"item": n, "qty": 1, "price": p} for n, p in MENU[rest["id"]][:2]]

o = repo.place_order("cust-777", rest, items)
print(f"1. placed {o['id']} total={o['total']}  ({repo.last_ru():.2f} RU)")

for s in ["ACCEPTED", "PREPARING", "OUT_FOR_DELIVERY", "DELIVERED"]:
    repo.update_status("cust-777", o["id"], s)
    print(f"2. -> {s:<17} ({repo.last_ru():.2f} RU)")

try:
    repo.update_status("cust-777", o["id"], "PREPARING")
except InvalidTransition as e:
    print("3. blocked:", e)

o2 = repo.place_order("cust-777", rest, items[:1])
try:
    repo.cancel_if_not_accepted("cust-777", o2["id"])
    print(f"4. {o2['id']} cancelled while still PLACED")
except Exception as e:      # emulator without conditional-patch support
    print(f"4. conditional patch not supported here ({type(e).__name__}) - show this step on Azure")

o3 = repo.place_order("cust-777", rest, items[:1])
repo.update_status("cust-777", o3["id"], "ACCEPTED")
try:
    repo.cancel_if_not_accepted("cust-777", o3["id"])
    print(f"5. WARNING: {o3['id']} was cancelled after ACCEPTED - this database ignored the filter")
    print("   predicate (some emulator versions do). On Azure Cosmos DB this step is blocked.")
except InvalidTransition as e:
    print(f"5. {o3['id']}: {e}")
except Exception as e:      # emulator without conditional-patch support
    print(f"5. conditional patch not supported here ({type(e).__name__}) - show this step on Azure")

page, token = repo.my_orders("cust-777", page_size=2)
print("6. my orders page 1:", [(p["id"], p["status"]) for p in page], "| more pages:", bool(token))

print("7. full history:", [h["status"] for h in repo.get("cust-777", o["id"])["history"]])
for x in (o, o2, o3):
    repo.delete("cust-777", x["id"])
print("8. cleaned up")
