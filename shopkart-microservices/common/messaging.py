"""
common/messaging.py
-------------------
A tiny "message queue" helper used by the Order Service (sender) and the
Order Worker (receiver).

Same 3 methods for every backend -> the rest of the code never changes:
    queue.send(message_dict)
    queue.receive(max_messages) -> list[dict]
    queue.count() -> int   (local only, for demos)

Backends:
    LocalQueue        -> SQLite file. Works offline, perfect for class.
    StorageQueue      -> Azure Storage Queue (simple, cheap, huge scale)
    ServiceBusQueue   -> Azure Service Bus (enterprise: DLQ, topics, sessions)

Real-life idea: Swiggy's "order placed" event goes into a queue. The restaurant
app, the delivery-partner app and the notification system each pick it up when
they are ready. The customer's checkout does NOT wait for all of them.
"""
import json
import sqlite3
import threading
from contextlib import contextmanager

from common.azure_clients import queue_client, servicebus_client
from common.config import settings


# --- [6.1] LocalQueue: a queue in a SQLite file ---
class LocalQueue:
    """First-in-first-out queue stored in a SQLite file (safe across processes)."""

    def __init__(self, name: str, db_file: str | None = None):
        self.name = name
        self.db_file = db_file or settings.local_queue_file
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS messages ("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " queue TEXT NOT NULL,"
                " body TEXT NOT NULL)"
            )

    @contextmanager
    def _connect(self):
        """Open the file, give the connection, then save (commit) and close it."""
        conn = sqlite3.connect(self.db_file, timeout=10)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def send(self, message: dict) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO messages (queue, body) VALUES (?, ?)",
                (self.name, json.dumps(message)),
            )

    def receive(self, max_messages: int = 5) -> list[dict]:
        """Take up to `max_messages` from the front of the queue (oldest first)."""
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT id, body FROM messages WHERE queue = ? ORDER BY id LIMIT ?",
                (self.name, max_messages),
            ).fetchall()
            for row_id, _ in rows:
                conn.execute("DELETE FROM messages WHERE id = ?", (row_id,))
        return [json.loads(body) for _, body in rows]

    def count(self) -> int:
        with self._connect() as conn:
            (n,) = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE queue = ?", (self.name,)
            ).fetchone()
        return n


# --- [6.2] StorageQueue: Azure Storage Queue ---
class StorageQueue:
    """Azure Storage Queue. Uses a connection string OR Managed Identity."""

    def __init__(self, name: str):
        from azure.core.exceptions import ResourceExistsError

        self.client = queue_client(name)
        try:
            self.client.create_queue()
        except ResourceExistsError:
            pass  # queue already exists -> fine

    def send(self, message: dict) -> None:
        self.client.send_message(json.dumps(message))

    def receive(self, max_messages: int = 5) -> list[dict]:
        result = []
        for msg in self.client.receive_messages(messages_per_page=max_messages, max_messages=max_messages):
            result.append(json.loads(msg.content))
            self.client.delete_message(msg)  # remove it so nobody processes it twice
        return result

    def count(self) -> int:
        return self.client.get_queue_properties().approximate_message_count


# --- [6.3] ServiceBusQueue: Azure Service Bus ---
class ServiceBusQueue:
    """Azure Service Bus queue. Uses a connection string OR Managed Identity."""

    def __init__(self, name: str):
        self.name = name
        self.client = servicebus_client()

    def send(self, message: dict) -> None:
        from azure.servicebus import ServiceBusMessage

        with self.client.get_queue_sender(self.name) as sender:
            sender.send_messages(
                ServiceBusMessage(json.dumps(message), subject=message.get("event", "event"))
            )

    def receive(self, max_messages: int = 5) -> list[dict]:
        result = []
        with self.client.get_queue_receiver(self.name, max_wait_time=2) as receiver:
            for msg in receiver.receive_messages(max_message_count=max_messages, max_wait_time=2):
                result.append(json.loads(b"".join(msg.body).decode("utf-8")))
                receiver.complete_message(msg)  # tell Service Bus "done, delete it"
        return result

    def count(self) -> int:
        return -1  # needs the management client; check in Azure Portal instead


# --- [6.4] get_queue(): pick the backend from settings ---
def get_queue(name: str | None = None):
    """Factory: returns the right queue object based on QUEUE_BACKEND in .env"""
    backend = settings.queue_backend
    if backend == "storage_queue":
        return StorageQueue(name or settings.queue_name)
    if backend == "service_bus":
        return ServiceBusQueue(name or settings.servicebus_queue)
    return LocalQueue(name or settings.queue_name)
