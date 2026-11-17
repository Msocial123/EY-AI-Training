"""
LAB 3 - Consistency levels in action
====================================
Curriculum topic : "Consistency Levels"

The 5 levels (strongest -> weakest). Stronger = more correct, slower, costlier.

  STRONG            Everyone always sees the latest write.
                    ShopKart: the last iPhone in stock during a flash sale.
  BOUNDED STALENESS Reads may lag by at most K versions or T seconds.
                    ShopKart: "Only 3 left!" counter - a few seconds old is fine.
  SESSION (default) YOU always see YOUR OWN writes (read-your-writes).
                    ShopKart: add to cart -> refresh -> item MUST be in the cart.
  CONSISTENT PREFIX Never see writes out of order (may be a bit behind).
                    ShopKart: order timeline Placed -> Packed -> Shipped, never Shipped before Packed.
  EVENTUAL          Will catch up "eventually"; cheapest + fastest.
                    ShopKart: review count "1,245 ratings", product view counters.

What this script shows:
  1. The account's DEFAULT consistency level
  2. A client that RELAXES consistency to Eventual (allowed) - and why it is cheaper
  3. Session tokens: how a SECOND app server gets read-your-writes for the same user
  4. A decision helper you can reuse in design discussions

Run:  python labs/lab03_consistency_levels.py
"""
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import config  # noqa: E402
from common.clients import cosmos_client, last_request_charge  # noqa: E402
from common.pretty import banner, step, info, ok, warn, table  # noqa: E402

LEVELS = [
    {"level": "Strong", "guarantee": "Always latest committed write", "RU_per_read": "2x",
     "shopkart_use": "Flash-sale stock, payment status"},
    {"level": "BoundedStaleness", "guarantee": "Lag <= K versions / T seconds", "RU_per_read": "2x",
     "shopkart_use": "'Only 3 left' banner, price in multi-region"},
    {"level": "Session", "guarantee": "Read-your-own-writes per session", "RU_per_read": "1x",
     "shopkart_use": "Cart, wishlist, profile, 'My Orders'"},
    {"level": "ConsistentPrefix", "guarantee": "Never out-of-order", "RU_per_read": "1x",
     "shopkart_use": "Order tracking timeline, chat messages"},
    {"level": "Eventual", "guarantee": "Converges eventually", "RU_per_read": "1x",
     "shopkart_use": "Ratings count, 'people viewing now', likes"},
]


def show_account_default():
    step("1) What is the account's DEFAULT consistency level?")
    client = cosmos_client()
    try:
        account = client.get_database_account()
        policy = getattr(account, "ConsistencyPolicy", {}) or {}
        default = policy.get("defaultConsistencyLevel", "unknown")
        ok(f"Account default = {default}")
        if default == "BoundedStaleness":
            info(f"maxStaleness: {policy.get('maxStalenessPrefix')} versions / {policy.get('maxIntervalInSeconds')} s")
    except Exception as e:  # emulator builds may not expose this
        warn(f"Could not read account settings ({type(e).__name__}). New Azure accounts default to Session.")
    info("Change it in Portal: Cosmos DB account > Settings > Default consistency.")


def relaxed_client_demo():
    step("2) Ratings widget: relax THIS client to Eventual (cheaper reads, may be slightly stale)")
    eventual = cosmos_client(consistency_level="Eventual")
    container = eventual.get_database_client(config.COSMOS_DATABASE).get_container_client("products")
    item = container.read_item("BOOK-4001", partition_key="Books")
    ok(f"read '{item['name']}' rating={item['rating']} with Eventual | cost {last_request_charge(container)}")
    warn("A client may only choose a level WEAKER than the account default (Strong > ... > Eventual).")
    warn("Asking for Strong on a Session account raises an error - you must change the account instead.")


def session_token_demo():
    step("3) Session consistency: cart written by server A, read by server B")
    info("Real life: ShopKart runs 4 web servers behind a load balancer.")
    info("Ananya adds a saree to her cart -> request hits server A.")
    info("She refreshes -> request hits server B. Will B see the cart item?")

    server_a = cosmos_client(consistency_level="Session")
    server_b = cosmos_client(consistency_level="Session")
    cont_a = server_a.get_database_client(config.COSMOS_DATABASE).get_container_client("orders")
    cont_b = server_b.get_database_client(config.COSMOS_DATABASE).get_container_client("orders")

    captured = {}

    def remember_session(headers, _body):
        captured["token"] = headers.get("x-ms-session-token")

    cart = {
        "id": f"CART-{uuid.uuid4().hex[:6]}",
        "customerId": "CUST-001",
        "type": "cart",
        "items": [{"sku": "FASH-2002", "qty": 1}],
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    cont_a.create_item(cart, response_hook=remember_session)
    token = captured.get("token")
    ok(f"Server A wrote {cart['id']}; session token = {str(token)[:40]}...")
    info("Server A puts this token in Ananya's cookie / response header.")

    item = cont_b.read_item(cart["id"], partition_key="CUST-001", session_token=token)
    ok(f"Server B read with the token -> sees {item['items']}  (read-your-writes guaranteed)")
    warn("Without the token, server B in another region could briefly read an older version.")
    warn("In one region you will not 'see' staleness - the guarantee matters at global scale.")

    cont_a.delete_item(cart["id"], partition_key="CUST-001")
    info("(demo cart deleted)")


def chooser():
    step("4) Cheat sheet - choose a level by asking 'what breaks if this read is old?'")
    table(LEVELS)
    info("Most real apps (incl. most e-commerce) keep the default SESSION level.")


def main():
    banner("LAB 3 - Consistency levels (ShopKart)")
    if config.IS_COSMOS_EMULATOR:
        warn("Emulator = single local replica, so every level behaves the same here.")
        warn("The CODE is identical on Azure; the GUARANTEES differ with multiple regions.")
    show_account_default()
    relaxed_client_demo()
    session_token_demo()
    chooser()
    banner("LAB 3 complete")


if __name__ == "__main__":
    main()
