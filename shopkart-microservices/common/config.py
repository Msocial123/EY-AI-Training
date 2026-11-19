"""
common/config.py
----------------
ONE place for every setting used by every ShopKart service.

Real-life idea: Flipkart/Amazon never hard-code URLs or passwords inside code.
They read them from environment variables (or Azure App Configuration / Key Vault).
Locally we keep them in a `.env` file (copy `.env.example` -> `.env`).
"""
import os

from dotenv import load_dotenv

load_dotenv()  # reads the .env file (if present) into environment variables


class Settings:
    # --- Where each microservice lives (used by services that call each other) ---
    product_service_url: str = os.getenv("PRODUCT_SERVICE_URL", "http://127.0.0.1:8001")
    order_service_url: str = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:8002")
    inventory_service_url: str = os.getenv("INVENTORY_SERVICE_URL", "http://127.0.0.1:8003")

    # --- Messaging: which queue technology should we use? ---
    # local         -> SQLite file on your laptop (no Azure needed)
    # storage_queue -> Azure Storage Queue
    # service_bus   -> Azure Service Bus queue
    queue_backend: str = os.getenv("QUEUE_BACKEND", "local")
    queue_name: str = os.getenv("QUEUE_NAME", "orders-queue")
    local_queue_file: str = os.getenv("LOCAL_QUEUE_FILE", "local_queue.db")

    # --- Azure Storage (Blob + Queue) ---
    # Option A (learning only): connection string that contains the account KEY
    storage_connection_string: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    # Option B (production): account name only + Managed Identity / az login (no secrets!)
    storage_account_name: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")

    # --- Azure Service Bus ---
    servicebus_connection_string: str = os.getenv("SERVICEBUS_CONNECTION_STRING", "")
    servicebus_namespace: str = os.getenv("SERVICEBUS_NAMESPACE", "")  # e.g. sb-shopkart-1234
    servicebus_queue: str = os.getenv("SERVICEBUS_QUEUE", "orders")


settings = Settings()
