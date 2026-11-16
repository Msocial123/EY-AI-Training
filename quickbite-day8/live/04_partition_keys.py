"""LIVE 4 - Same data, three partition keys   (Module 8.5)"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from collections import Counter
from qb.config import get_container, query, title
from qb.seed_data import orders as make_orders

title("LIVE 4 - Partition key showdown")
data = make_orders()
candidates = {"/status": "OrdersByStatus", "/city": "OrdersByCity", "/customerId": "OrdersByCustomer"}

for path, name in candidates.items():
    field = path.strip("/")
    c = get_container(name, path)
    for o in data:
        c.upsert_item(o)
    spread = Counter(o[field] for o in data)
    biggest = spread.most_common(1)[0]
    print(f"\n{path:<12} distinct values={len(spread):<4} largest partition={biggest[0]} ({biggest[1]} of {len(data)} orders)")

    # The query the app runs most: "show MY orders" (customer cust-007)
    if path == "/customerId":
        _, cost = query(c, "SELECT * FROM c WHERE c.customerId = 'cust-007'", pk="cust-007")
        print(f"   'my orders' query -> {cost} RU (single partition)")
    else:
        _, cost = query(c, "SELECT * FROM c WHERE c.customerId = 'cust-007'")
        print(f"   'my orders' query -> {cost} RU (cross-partition fan-out)")

if cost == 0:
    print("\n(RU = 0 means you are on the local emulator - it does not measure RUs.")
    print(" On Azure the cross-partition queries cost clearly more than the single-partition one.)")

print("""
VERDICT
  /status     -> 6 values: low cardinality, 'PLACED' is a hot partition at dinner time
  /city       -> 5 values: Bengaluru grows forever, 20 GB logical-partition limit
  /customerId -> 25+ values (millions in prod), even spread, matches 'my orders'  OK""")
