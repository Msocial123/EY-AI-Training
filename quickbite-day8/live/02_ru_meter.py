"""LIVE 2 - The RU meter: what does each operation cost?   (Module 8.3)
Ask the room to GUESS each number before you press Enter."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from qb.config import get_container, ru, query, title, on_emulator
from qb.seed_data import orders as make_orders

title("LIVE 2 - RU meter")
c = get_container("Orders", "/customerId")
print("Seeding 120 orders...")
for o in make_orders():
    c.upsert_item(o)

rows = []
def log(label, value): rows.append((label, value))

first = make_orders()[0]
c.read_item(first["id"], partition_key=first["customerId"]); log("Point read (id + pk)", ru(c))
log("Query by id, NO pk (fan-out)", query(c, "SELECT * FROM c WHERE c.id = @i", [{"name": "@i", "value": first["id"]}])[1])
log("Query in ONE partition", query(c, "SELECT * FROM c", pk="cust-001")[1])
log("Same, projecting 2 fields", query(c, "SELECT c.id, c.total FROM c", pk="cust-001")[1])
log("SELECT * whole container", query(c, "SELECT * FROM c")[1])

small = {"id": "ru-small", "customerId": "cust-999", "note": "hi"}
c.upsert_item(small); log("Write ~0.1 KB item", ru(c))
big = {"id": "ru-big", "customerId": "cust-999", "blob": "x" * 50_000}
c.upsert_item(big); log("Write ~50 KB item", ru(c))
c.patch_item("ru-small", "cust-999", [{"op": "set", "path": "/note", "value": "patched"}]); log("Patch one field", ru(c))
c.delete_item("ru-small", partition_key="cust-999"); log("Delete small item", ru(c))
c.delete_item("ru-big", partition_key="cust-999")

print()
for label, v in rows:
    print(f"  {label:<32} {v:>7.2f} RU  {'#' * min(60, max(1, int(v)))}")

# Capacity planning on REAL measured numbers
read_ru, write_ru = rows[0][1], rows[5][1]
if read_ru == 0:   # the local emulator does not measure RUs
    print("\nNOTE: RU shows 0 because the local emulator does not measure Request Units.")
    print("      Using typical Azure values instead: point read = 1 RU, small write = 8 RU.")
    read_ru, write_ru = 1.0, 8.0
peak_reads, peak_writes = 800, 120          # QuickBite dinner peak (per second)
need = (peak_reads * read_ru + peak_writes * write_ru) * 1.3
print(f"\nDinner peak: {peak_reads} reads/s + {peak_writes} writes/s -> ~{need:,.0f} RU/s incl. 30% headroom")
