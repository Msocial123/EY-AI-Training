"""
LAB 7 - Azure Blob Storage with the Python SDK
==============================================
Curriculum topic : "Accessing Blob storage through SDK"

Blob = Binary Large OBject = any file: images, PDFs, videos, backups, CSV exports.

Hierarchy
  Storage ACCOUNT  (shopkartstore)            -> like a hard disk
    CONTAINER      (product-images)           -> like a top-level folder (lowercase!)
      BLOB         (electronics/ELEC-1001.png) -> the file. '/' makes VIRTUAL folders

Why not keep images inside Cosmos DB?  A 2 MB image in Cosmos = expensive RU + 2 MB
item limit. Rule: FILES go to Blob, the URL/metadata of the file goes to Cosmos DB.

ShopKart tasks in this lab
  1. Create containers: product-images, invoices
  2. Upload product photos with the right Content-Type + metadata (sku, category)
  3. List blobs "inside a folder" with a prefix (= list all Electronics images)
  4. Read properties/metadata without downloading the file
  5. Download a blob
  6. Change access tier Hot -> Cool for old invoices (cheaper storage)
  7. Delete a discontinued product's image

Run:  python labs/lab07_blob_storage_sdk.py      (Azurite or real Azure)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError, HttpResponseError  # noqa: E402
from azure.storage.blob import ContentSettings  # noqa: E402

from common import config  # noqa: E402
from common.clients import blob_service_client  # noqa: E402
from common.pretty import banner, step, info, ok, warn, table  # noqa: E402

DOWNLOADS = config.ROOT / "downloads"
CATEGORY_FOLDER = {"ELEC": "electronics", "FASH": "fashion", "HOME": "home-kitchen", "BOOK": "books", "GROC": "grocery"}


def create_containers(service):
    step("1) Create containers (private by default - nobody can read without auth)")
    for name in ("product-images", "invoices"):
        try:
            service.create_container(name)
            ok(f"created '{name}'")
        except ResourceExistsError:
            ok(f"'{name}' already exists")


def upload_product_images(service):
    step("2) Upload product photos with Content-Type and metadata")
    container = service.get_container_client("product-images")
    for img in sorted((config.ASSETS_DIR / "product_images").glob("*.png")):
        sku = img.stem
        blob_name = f"{CATEGORY_FOLDER[sku[:4]]}/{sku}.png"     # virtual folder per category
        with open(img, "rb") as data:
            container.upload_blob(
                name=blob_name,
                data=data,
                overwrite=True,                                   # re-running the lab is safe
                content_settings=ContentSettings(content_type="image/png", cache_control="public, max-age=86400"),
                metadata={"sku": sku, "uploadedBy": "catalog-team"},
            )
        info(f"uploaded {blob_name}")
    ok("Without content_type the browser would DOWNLOAD the image instead of SHOWING it.")

    step("   Also upload the supplier invoice into 'invoices/2026/11/'")
    inv = service.get_blob_client("invoices", "2026/11/TN-INV-2026-0457.pdf")
    with open(config.ASSETS_DIR / "invoice_technova.pdf", "rb") as data:
        inv.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type="application/pdf"),
                        metadata={"vendor": "TechNova", "status": "received"})
    ok(f"uploaded {inv.blob_name}")


def list_blobs(service):
    step("3) List ALL blobs, then only the 'electronics/' folder (prefix filter)")
    container = service.get_container_client("product-images")
    rows = [{"name": b.name, "size_KB": round(b.size / 1024, 1), "type": b.content_settings.content_type}
            for b in container.list_blobs()]
    table(rows)
    electronics = [b.name for b in container.list_blobs(name_starts_with="electronics/")]
    ok(f"electronics/ has {len(electronics)} images: {electronics}")

    step("   Folder view: walk_blobs() shows virtual folders like a file explorer")
    for item in container.walk_blobs(delimiter="/"):
        info(f"[folder] {item.name}")


def properties_and_download(service):
    step("4) Read properties + metadata WITHOUT downloading the file")
    blob = service.get_blob_client("product-images", "electronics/ELEC-1001.png")
    props = blob.get_blob_properties()
    info(f"size={props.size} bytes | type={props.content_settings.content_type} | etag={props.etag}")
    info(f"last_modified={props.last_modified} | tier={props.blob_tier} | metadata={props.metadata}")

    step("5) Download the blob to ./downloads/")
    DOWNLOADS.mkdir(exist_ok=True)
    target = DOWNLOADS / "ELEC-1001.png"
    with open(target, "wb") as f:
        f.write(blob.download_blob().readall())
    ok(f"saved {target.relative_to(config.ROOT)} ({target.stat().st_size} bytes)")
    info(f"Blob URL (private - opening it in a browser gives 'ResourceNotFound/AuthorizationFailed'):")
    info(blob.url)


def change_tier(service):
    step("6) Move last month's invoice to the COOL tier (cheaper storage, costlier reads)")
    blob = service.get_blob_client("invoices", "2026/11/TN-INV-2026-0457.pdf")
    try:
        blob.set_standard_blob_tier("Cool")
        ok(f"tier now: {blob.get_blob_properties().blob_tier}")
    except HttpResponseError as e:
        warn(f"Tier change not supported here ({e.reason}). Works on Azure Standard GPv2 accounts.")
    info("Hot = frequently read (product images) | Cool = 30+ days | Cold = 90+ | Archive = 180+ (offline)")
    info("Automate it: Portal > Storage account > Lifecycle management rule.")
    blob.set_blob_metadata({"vendor": "TechNova", "status": "archived-cool"})


def delete_blob(service):
    step("7) Product discontinued -> delete its image (and handle 'already deleted')")
    blob = service.get_blob_client("product-images", "fashion/FASH-2004.png")
    info(f"exists before delete? {blob.exists()}")
    blob.delete_blob()
    ok(f"deleted {blob.blob_name}")
    try:
        blob.delete_blob()
    except ResourceNotFoundError:
        ok("second delete -> ResourceNotFoundError, handled gracefully")


def main():
    banner("LAB 7 - Blob Storage SDK (ShopKart files)")
    info(f"Target: {'Azurite (local emulator)' if config.IS_AZURITE else 'Azure Storage account'}")
    service = blob_service_client()
    info(f"Account: {service.account_name}  |  URL: {service.url}")
    create_containers(service)
    upload_product_images(service)
    list_blobs(service)
    properties_and_download(service)
    change_tier(service)
    delete_blob(service)
    banner("LAB 7 complete - next: share these PRIVATE files safely with SAS links (lab 8)")


if __name__ == "__main__":
    main()
