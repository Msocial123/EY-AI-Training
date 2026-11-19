"""
common/azure_clients.py
-----------------------
Creates Azure SDK clients in ONE place, with two ways to log in:

  1. Connection string  -> contains the account KEY (like a master password).
                           OK for learning, NOT recommended in production.
  2. DefaultAzureCredential -> NO secrets in code or .env.
        * on your laptop it uses your `az login`
        * inside Azure (VM, App Service, Container Apps, Functions) it uses
          the resource's MANAGED IDENTITY automatically.
     Same code works in both places - that's the magic.
"""
from common.config import settings


# --- [5.1] One credential object for everything ---
def get_credential():
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


# --- [5.2] Blob Storage client ---
def blob_service_client():
    from azure.storage.blob import BlobServiceClient

    if settings.storage_connection_string:
        return BlobServiceClient.from_connection_string(settings.storage_connection_string)
    account_url = f"https://{settings.storage_account_name}.blob.core.windows.net"
    return BlobServiceClient(account_url, credential=get_credential())


# --- [5.3] Storage Queue client ---
def queue_client(queue_name: str):
    from azure.storage.queue import QueueClient

    if settings.storage_connection_string:
        return QueueClient.from_connection_string(settings.storage_connection_string, queue_name)
    account_url = f"https://{settings.storage_account_name}.queue.core.windows.net"
    return QueueClient(account_url, queue_name, credential=get_credential())


# --- [5.4] Service Bus client ---
def servicebus_client():
    from azure.servicebus import ServiceBusClient

    if settings.servicebus_connection_string:
        return ServiceBusClient.from_connection_string(settings.servicebus_connection_string)
    return ServiceBusClient(
        f"{settings.servicebus_namespace}.servicebus.windows.net",
        credential=get_credential(),
    )
