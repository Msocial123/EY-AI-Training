"""
azure_demos/service_bus_demo.py   ->   Module 6: Azure Service Bus

Two patterns you will use in real projects:

  QUEUE  (one message -> ONE receiver)
      "Charge this payment" must happen exactly once.

  TOPIC + SUBSCRIPTIONS  (one message -> EVERY subscription gets a copy)
      "OrderPlaced" -> email-sub sends the email
                    -> analytics-sub updates the sales dashboard

Run (from the project root):
    python -m azure_demos.service_bus_demo queue-send
    python -m azure_demos.service_bus_demo queue-receive
    python -m azure_demos.service_bus_demo dead-letters
    python -m azure_demos.service_bus_demo topic-send
    python -m azure_demos.service_bus_demo topic-receive email-sub
    python -m azure_demos.service_bus_demo topic-receive analytics-sub
"""
import json
import os
import sys

from azure.servicebus import ServiceBusMessage, ServiceBusSubQueue

from common.azure_clients import servicebus_client
from common.config import settings

QUEUE = settings.servicebus_queue                      # "orders"
TOPIC = os.getenv("SERVICEBUS_TOPIC", "order-events")  # needs Standard tier


def body_of(msg) -> dict:
    return json.loads(b"".join(msg.body).decode("utf-8"))


# --- [6.10] Queue: send (one good message, one broken message) ---
def queue_send() -> None:
    good = {"event": "OrderPlaced", "order_id": 501, "amount": 2797}
    bad = {"event": "OrderPlaced", "order_id": None}  # broken: no order id
    with servicebus_client() as client, client.get_queue_sender(QUEUE) as sender:
        for data in (good, bad):
            sender.send_messages(
                ServiceBusMessage(
                    json.dumps(data),
                    subject="OrderPlaced",
                    application_properties={"source": "order-service"},
                )
            )
            print(f"Sent to queue '{QUEUE}': {data}")


# --- [6.11] Queue: receive with PEEK-LOCK, complete or dead-letter ---
def queue_receive() -> None:
    with servicebus_client() as client, client.get_queue_receiver(QUEUE, max_wait_time=5) as receiver:
        for msg in receiver:
            data = body_of(msg)
            print(f"Received: {data}  (delivery_count={msg.delivery_count})")
            if data.get("order_id") is None:
                receiver.dead_letter_message(
                    msg, reason="InvalidOrder", error_description="order_id is missing"
                )
                print("   -> moved to DEAD-LETTER queue")
            else:
                receiver.complete_message(msg)
                print("   -> processed, completed (deleted)")


def dead_letters() -> None:
    with servicebus_client() as client, client.get_queue_receiver(
        QUEUE, sub_queue=ServiceBusSubQueue.DEAD_LETTER, max_wait_time=5
    ) as receiver:
        for msg in receiver:
            print(f"DLQ: {body_of(msg)}  reason={msg.dead_letter_reason}")
            receiver.complete_message(msg)


# --- [6.12] Topic: publish once, every subscription gets a copy ---
def topic_send() -> None:
    event = {"event": "OrderPlaced", "order_id": 777, "customer": "Ravi", "amount": 69999}
    with servicebus_client() as client, client.get_topic_sender(TOPIC) as sender:
        sender.send_messages(ServiceBusMessage(json.dumps(event), subject="OrderPlaced"))
    print(f"Published to topic '{TOPIC}': {event}")


def topic_receive(subscription: str) -> None:
    with servicebus_client() as client, client.get_subscription_receiver(
        TOPIC, subscription, max_wait_time=5
    ) as receiver:
        for msg in receiver:
            print(f"[{subscription}] got {body_of(msg)}")
            receiver.complete_message(msg)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "queue-send"
    actions = {
        "queue-send": queue_send,
        "queue-receive": queue_receive,
        "dead-letters": dead_letters,
        "topic-send": topic_send,
    }
    if cmd == "topic-receive":
        topic_receive(sys.argv[2] if len(sys.argv) > 2 else "email-sub")
    else:
        actions[cmd]()
