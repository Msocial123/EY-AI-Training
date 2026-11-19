"""
workers/order_worker.py   ->   Background worker (the "consumer")

Run:   python -m workers.order_worker

It loops forever:
   1. take "OrderPlaced" messages from the queue
   2. reserve stock in the INVENTORY service (Flask)
   3. tell the ORDER service: CONFIRMED or FAILED
   4. "send" an email (we just print it)

If the inventory service is DOWN, the message is put back with attempt+1.
After 3 failed attempts it goes to a DEAD-LETTER queue for a human to check.
This is exactly how Azure Service Bus works (MaxDeliveryCount + DLQ).
"""
import time

import httpx

from common.config import settings
from common.messaging import get_queue

MAX_ATTEMPTS = 3


# --- [6.5] Process ONE message ---
def process_order_message(message: dict) -> str:
    """Returns the final status we set: CONFIRMED or FAILED."""
    order_id = message["order_id"]
    reserved = []  # remember what we reserved, so we can undo it

    for item in message["items"]:
        resp = httpx.post(
            f"{settings.inventory_service_url}/inventory/reserve",
            json={"order_id": order_id, **item},
            timeout=5,
        )
        if resp.status_code == 200:
            reserved.append(item)
            continue

        # Out of stock -> undo earlier reservations (a "compensating action")
        for done in reserved:
            httpx.post(f"{settings.inventory_service_url}/inventory/restock", json=done, timeout=5)
        reason = resp.json().get("error", "stock problem")
        set_order_status(order_id, "FAILED", f"{reason} for product {item['product_id']}")
        print(f"   [EMAIL] to {message['email']}: Sorry, order #{order_id} could not be confirmed.")
        return "FAILED"

    set_order_status(order_id, "CONFIRMED", "Stock reserved, packing soon")
    print(f"   [EMAIL] to {message['email']}: Yay! Order #{order_id} is confirmed.")
    return "CONFIRMED"


def set_order_status(order_id: int, status: str, note: str) -> None:
    httpx.patch(
        f"{settings.order_service_url}/orders/{order_id}/status",
        json={"status": status, "note": note},
        timeout=5,
    )


# --- [6.6] The forever loop with retry + dead-letter ---
def run_forever(poll_seconds: float = 2.0) -> None:
    queue = get_queue()
    dead_letter = get_queue(f"{settings.queue_name}-deadletter")
    print(f"Order worker started. Backend={settings.queue_backend}. Waiting for messages...")

    while True:
        messages = queue.receive(max_messages=5)
        for msg in messages:
            print(f"-> Got {msg['event']} for order #{msg['order_id']} (attempt {msg['attempt']})")
            try:
                result = process_order_message(msg)
                print(f"   Order #{msg['order_id']} -> {result}")
            except httpx.RequestError as err:
                print(f"   A service is down: {err.__class__.__name__}")
                if msg["attempt"] < MAX_ATTEMPTS:
                    queue.send({**msg, "attempt": msg["attempt"] + 1})  # retry later
                    print("   Put back in queue for retry")
                else:
                    dead_letter.send({**msg, "reason": str(err)})
                    print("   Moved to DEAD-LETTER queue")
        time.sleep(poll_seconds)


if __name__ == "__main__":
    run_forever()
