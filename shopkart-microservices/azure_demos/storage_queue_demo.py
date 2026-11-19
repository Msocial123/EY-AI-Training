"""
azure_demos/storage_queue_demo.py   ->   Module 6: Azure Storage Queue

Real-life: Big Billion Days sale. 10,000 orders per second arrive. The order
API writes each order to a queue in milliseconds. Workers drain the queue at
their own speed. Nobody's checkout fails because the warehouse system is slow.

Run (from the project root), step by step in class:
    python -m azure_demos.storage_queue_demo send 5     # producer: 5 orders
    python -m azure_demos.storage_queue_demo peek       # look, don't touch
    python -m azure_demos.storage_queue_demo receive    # consumer: process + delete
    python -m azure_demos.storage_queue_demo crash      # receive but DON'T delete
"""
import json
import random
import sys

from azure.core.exceptions import ResourceExistsError

from common.azure_clients import queue_client

QUEUE_NAME = "orders-queue"


def get_queue():
    client = queue_client(QUEUE_NAME)
    try:
        client.create_queue()
    except ResourceExistsError:
        pass
    return client


# --- [6.7] Producer: send messages ---
def send(count: int) -> None:
    client = get_queue()
    for _ in range(count):
        message = {
            "event": "OrderPlaced",
            "order_id": random.randint(1000, 9999),
            "amount": random.choice([399, 1099, 2797, 69999]),
        }
        client.send_message(json.dumps(message))
        print(f"Sent: {message}")
    props = client.get_queue_properties()
    print(f"Approx messages in queue: {props.approximate_message_count}")


# --- [6.8] Peek: read without removing ---
def peek() -> None:
    for msg in get_queue().peek_messages(max_messages=10):
        print(f"[peek] {msg.content}")


# --- [6.9] Consumer: receive -> process -> delete ---
def receive(delete: bool = True) -> None:
    client = get_queue()
    # visibility_timeout: the message is HIDDEN from other workers for 30s
    for msg in client.receive_messages(messages_per_page=5, visibility_timeout=30, max_messages=5):
        order = json.loads(msg.content)
        print(f"Processing order {order['order_id']} (dequeue_count={msg.dequeue_count})")
        if delete:
            client.delete_message(msg)
            print("   done -> deleted")
        else:
            print("   worker CRASHED before delete -> message will come back after 30s")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "peek"
    if cmd == "send":
        send(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    elif cmd == "receive":
        receive(delete=True)
    elif cmd == "crash":
        receive(delete=False)
    else:
        peek()
