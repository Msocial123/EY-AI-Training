"""Optional: upload pipeline outputs to Azure Blob Storage (reuses the Day 9 Blob SDK skill)."""
import os
from datetime import date
from pathlib import Path


def upload_to_blob(folder, container_name, logger):
    """Upload every file in folder to Azure Blob. Skips quietly if not configured."""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        logger.info("AZURE_STORAGE_CONNECTION_STRING not set - skipping Blob upload")
        return []
    uploaded = []
    try:
        from azure.storage.blob import BlobServiceClient

        service = BlobServiceClient.from_connection_string(connection_string)
        container = service.get_container_client(container_name)
        if not container.exists():
            container.create_container()
        for file in sorted(Path(folder).glob("*.*")):
            blob_name = f"{date.today():%Y-%m-%d}/{file.name}"
            with open(file, "rb") as data:
                container.upload_blob(name=blob_name, data=data, overwrite=True)
            uploaded.append(blob_name)
            logger.info("Uploaded %s to container %s", blob_name, container_name)
    except Exception as error:
        logger.error("Blob upload failed (data is still safe locally): %s", error)
    return uploaded
