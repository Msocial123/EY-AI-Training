"""
LAB 9 - CAPSTONE: ShopKart supplier-invoice pipeline (all Day 9 topics together)
================================================================================

   Vendor                    ShopKart backend                                   Finance team
   ------                    ----------------                                   ------------
 1. asks for upload link --> 2. creates write-only SAS (Blob + SAS)
 3. uploads PDF via SAS  --> Blob: vendor-uploads/technova/<file>.pdf
                             4. reads the PDF bytes (Blob SDK)
                             5. extracts fields (Document Intelligence / OCR)
                             6. PO match + confidence check
                             7. saves JSON to Cosmos DB 'invoices' (pk=/vendorName)
                             8. SQL query: all ON_HOLD invoices          -->  9. dashboard list
                             10. read-only SAS to view the original PDF   -->  clicks link

Works with: Azurite + Cosmos emulator + OFFLINE Document Intelligence (no Azure needed),
            or fully on Azure when keys are set.

Run:  python labs/lab09_capstone_invoice_pipeline.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from azure.storage.blob import (  # noqa: E402
    BlobSasPermissions, ContainerClient, ContainerSasPermissions, ContentSettings,
    generate_blob_sas, generate_container_sas,
)

from common import config  # noqa: E402
from common.clients import blob_service_client, cosmos_database, last_request_charge  # noqa: E402
from common.pretty import banner, step, info, ok, warn, table  # noqa: E402
import lab06_document_intelligence as docintel  # noqa: E402  (re-use the extraction logic)

VENDOR = "TechNova Supplies Pvt. Ltd."
FILE_NAME = "TN-INV-2026-0457.pdf"


def utc_now():
    return datetime.now(timezone.utc)


def main():
    banner("LAB 9 - Capstone: invoice pipeline")
    service = blob_service_client()
    key = service.credential.account_key
    try:
        service.create_container("vendor-uploads")
    except Exception:
        pass

    # 1-2. backend issues a write-only SAS
    step("1-2) Vendor portal asks backend for an upload link -> write-only SAS (10 min)")
    sas = generate_container_sas(service.account_name, "vendor-uploads", account_key=key,
                                 permission=ContainerSasPermissions(create=True, write=True),
                                 expiry=utc_now() + timedelta(minutes=10))
    upload_url = f"{service.url.rstrip('/')}/vendor-uploads?{sas}"
    ok("upload link issued")

    # 3. vendor uploads with nothing but the SAS URL
    step("3) Vendor uploads the PDF using ONLY the SAS link")
    blob_path = f"technova/{FILE_NAME}"
    ContainerClient.from_container_url(upload_url).upload_blob(
        blob_path, (config.ASSETS_DIR / "invoice_technova.pdf").read_bytes(), overwrite=True,
        content_settings=ContentSettings(content_type="application/pdf"))
    ok(f"stored at vendor-uploads/{blob_path}")

    # 4. backend reads the file with its own identity
    step("4) Backend downloads the PDF bytes with the Blob SDK")
    pdf_bytes = service.get_blob_client("vendor-uploads", blob_path).download_blob().readall()
    ok(f"{len(pdf_bytes)} bytes read")
    local_copy = config.ROOT / "downloads" / FILE_NAME
    local_copy.parent.mkdir(exist_ok=True)
    local_copy.write_bytes(pdf_bytes)

    # 5-6. extraction + validation (re-uses lab 6)
    step("5-6) Document Intelligence extraction + PO match (from lab 6)")
    record = docintel.invoice_demo(local_copy)
    record["blobContainer"] = "vendor-uploads"
    record["blobPath"] = blob_path
    record["processedAt"] = utc_now().isoformat()

    # 7. save to Cosmos DB
    step("7) Save the structured invoice to Cosmos DB container 'invoices'")
    try:
        invoices = cosmos_database().get_container_client("invoices")
        invoices.upsert_item(record)
        ok(f"saved id={record['id']} pk={record['vendorName']} | cost {last_request_charge(invoices)}")

        # 8. query
        step("8) Finance dashboard query: every invoice that needs attention")
        rows = list(invoices.query_items(
            query="SELECT c.id, c.vendorName, c.total, c.status, c.dueDate FROM c "
                  "WHERE c.status IN ('ON_HOLD', 'NEEDS_REVIEW') ORDER BY c.dueDate",
            enable_cross_partition_query=True))
        table(rows)
    except Exception as e:  # Cosmos emulator not running etc.
        warn(f"Cosmos DB not reachable ({type(e).__name__}). Start the emulator and run lab01 first.")
        warn("Pipeline continues so you can still see the SAS step.")

    # 10. read-only link for finance
    step("10) Finance clicks 'View original PDF' -> 30-minute read-only SAS")
    view_sas = generate_blob_sas(service.account_name, "vendor-uploads", blob_path, account_key=key,
                                 permission=BlobSasPermissions(read=True),
                                 expiry=utc_now() + timedelta(minutes=30))
    info(f"{service.url.rstrip('/')}/vendor-uploads/{blob_path}?{view_sas[:60]}...")
    ok("We store blobPath in Cosmos, NOT the SAS URL - SAS is generated fresh on every click.")

    banner(f"CAPSTONE complete -> invoice {record['id']} is {record['status']}")


if __name__ == "__main__":
    main()
