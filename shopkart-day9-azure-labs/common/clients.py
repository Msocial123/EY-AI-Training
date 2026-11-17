"""
One function per Azure service that returns a ready-to-use client.
Every lab imports from here, so connection logic lives in ONE place.
"""
from . import config


# ---------------------------------------------------------------- Cosmos DB --
def cosmos_client(consistency_level: str | None = None, key_env: str = "COSMOS_KEY"):
    """
    Returns a CosmosClient.

    - consistency_level: None = use the account default.
      You may only RELAX it per client (e.g. account=Session -> client=Eventual).
    - key_env: which env var holds the key (COSMOS_KEY or COSMOS_READONLY_KEY).
    - If USE_ENTRA_ID=true we log in with Microsoft Entra ID (no keys at all).
    """
    from azure.cosmos import CosmosClient

    kwargs = {}
    if consistency_level:
        kwargs["consistency_level"] = consistency_level
    if config.flag("COSMOS_DISABLE_SSL_VERIFY"):
        kwargs["connection_verify"] = False  # only for the HTTPS emulator's self-signed cert

    if config.flag("USE_ENTRA_ID"):
        from azure.identity import DefaultAzureCredential
        return CosmosClient(config.COSMOS_ENDPOINT, credential=DefaultAzureCredential(), **kwargs)

    key = config.require(key_env)
    return CosmosClient(config.COSMOS_ENDPOINT, credential=key, **kwargs)


def cosmos_database(client=None):
    client = client or cosmos_client()
    return client.get_database_client(config.COSMOS_DATABASE)


def last_request_charge(container) -> str:
    """Request Units (RU) charged for the LAST call made through this container."""
    try:
        headers = container.client_connection.last_response_headers or {}
        ru = headers.get("x-ms-request-charge")
        return f"{float(ru):.2f} RU" if ru is not None else "n/a (emulator does not report RU)"
    except Exception:
        return "n/a"


# ------------------------------------------------------------- Blob Storage --
def blob_service_client():
    from azure.storage.blob import BlobServiceClient

    if config.flag("USE_ENTRA_ID") and config.get("STORAGE_ACCOUNT_URL"):
        from azure.identity import DefaultAzureCredential
        return BlobServiceClient(config.get("STORAGE_ACCOUNT_URL"), credential=DefaultAzureCredential())
    return BlobServiceClient.from_connection_string(config.STORAGE_CONNECTION_STRING)


# ------------------------------------------------------- AI Vision (OCR) --
# NOTE: Image Analysis 4.0 is scheduled to retire on 25-Sep-2028. For new OCR work Microsoft
# recommends Document Intelligence "prebuilt-read" (lab 5 uses it automatically when its keys exist).
def vision_client():
    """Returns None when keys are missing -> labs fall back to OFFLINE mode."""
    if not (config.VISION_ENDPOINT and config.VISION_KEY):
        return None
    from azure.ai.vision.imageanalysis import ImageAnalysisClient
    from azure.core.credentials import AzureKeyCredential
    return ImageAnalysisClient(endpoint=config.VISION_ENDPOINT, credential=AzureKeyCredential(config.VISION_KEY))


# ------------------------------------------------ Document Intelligence --
def docintel_client():
    """Returns None when keys are missing -> labs fall back to OFFLINE mode."""
    if not (config.DOCINTEL_ENDPOINT and config.DOCINTEL_KEY):
        return None
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential
    return DocumentIntelligenceClient(endpoint=config.DOCINTEL_ENDPOINT, credential=AzureKeyCredential(config.DOCINTEL_KEY))
