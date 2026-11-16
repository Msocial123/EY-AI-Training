"""LIVE 7 - Two support agents edit the same order at once   (Module 8.6)
Part 1 shows the bug (lost update). Part 2 fixes it with the _etag."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from azure.core import MatchConditions
from azure.cosmos import exceptions
from qb.config import get_container, title

title("LIVE 7 - Lost update vs ETag")
c = get_container("Orders", "/customerId")
c.upsert_item({"id": "race-1", "customerId": "cust-500", "status": "PLACED", "total": 450})

# ---------------- PART 1: the bug
print("\nPART 1 - no protection")
agent_a = c.read_item("race-1", partition_key="cust-500")      # Agent A opens the order
agent_b = c.read_item("race-1", partition_key="cust-500")      # Agent B opens the same order
print("  both agents loaded version (etag):", agent_a["_etag"])

agent_a["status"] = "CANCELLED"                                 # customer asked A to cancel
c.replace_item("race-1", agent_a)
agent_b["status"] = "OUT_FOR_DELIVERY"                          # B still sees the OLD copy
c.replace_item("race-1", agent_b)
final = c.read_item("race-1", partition_key="cust-500")["status"]
print(f"  final status: {final}   <- A's cancellation is silently LOST")

# ---------------- PART 2: the fix
print("\nPART 2 - send the etag back with every write")
c.upsert_item({"id": "race-1", "customerId": "cust-500", "status": "PLACED", "total": 450})
agent_a = c.read_item("race-1", partition_key="cust-500")
agent_b = c.read_item("race-1", partition_key="cust-500")

agent_a["status"] = "CANCELLED"
c.replace_item("race-1", agent_a, etag=agent_a["_etag"], match_condition=MatchConditions.IfNotModified)
print("  Agent A saved (etag matched)")

agent_b["status"] = "OUT_FOR_DELIVERY"
try:
    c.replace_item("race-1", agent_b, etag=agent_b["_etag"], match_condition=MatchConditions.IfNotModified)
    print("  WARNING: Agent B also saved - this database did not check the etag (some emulator")
    print("  versions don't). On Azure Cosmos DB, B gets 412 here.")
except exceptions.CosmosHttpResponseError as e:
    if e.status_code != 412:
        raise
    print("  Agent B REJECTED: 412 Precondition Failed - the order changed since B opened it")
    print("  -> B's app re-reads the order, sees CANCELLED, and tells the agent")

print("  final status:", c.read_item("race-1", partition_key="cust-500")["status"])
c.delete_item("race-1", partition_key="cust-500")
