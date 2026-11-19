"""
azure_demos/blob_product_images.py   ->   Module 5: Azure Storage (Blob)

Real-life: every product photo you see on Myntra/Amazon is a file in blob
storage (behind a CDN). Here we upload ShopKart product images + a catalog file.

Run (from the project root):
    python -m azure_demos.blob_product_images upload
    python -m azure_demos.blob_product_images list
    python -m azure_demos.blob_product_images download iphone15.png

Login used: see common/azure_clients.py
   - AZURE_STORAGE_CONNECTION_STRING set  -> key-based
   - else AZURE_STORAGE_ACCOUNT_NAME      -> az login / Managed Identity
"""
import sys
from pathlib import Path

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import ContentSettings

from common.azure_clients import blob_service_client

CONTAINER = "product-images"
SAMPLE_DIR = Path("sample_data")
CONTENT_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".json": "application/json"}
FILES_TO_UPLOAD = ["iphone15.png", "nike-shoes.png", "basmati-rice.png", "products.json"]


# --- [5.5] Create the container (a "folder" for blobs) ---
def get_container():
    container = blob_service_client().get_container_client(CONTAINER)
    try:
        container.create_container()
        print(f"Created container '{CONTAINER}'")
    except ResourceExistsError:
        pass
    return container


# --- [5.6] Upload, list, download ---
def upload_all() -> None:
    container = get_container()
    for name in FILES_TO_UPLOAD:
        file = SAMPLE_DIR / name
        with open(file, "rb") as data:
            container.upload_blob(
                name=file.name,
                data=data,
                overwrite=True,
                content_settings=ContentSettings(content_type=CONTENT_TYPES[file.suffix]),
                metadata={"uploaded_by": "shopkart-day12", "category": "catalog"},
            )
        print(f"Uploaded {file.name}  ({file.stat().st_size} bytes)")


def list_all() -> None:
    container = get_container()
    print(f"Blobs in '{CONTAINER}':")
    for blob in container.list_blobs(include=["metadata"]):
        print(f"  {blob.name:<25} {blob.size:>8} bytes   {blob.content_settings.content_type}")


def download(name: str) -> None:
    container = get_container()
    target = Path("downloads") / name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(container.download_blob(name).readall())
    print(f"Downloaded {name} -> {target}")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "list"
    if command == "upload":
        upload_all()
    elif command == "download":
        download(sys.argv[2])
    else:
        list_all()
