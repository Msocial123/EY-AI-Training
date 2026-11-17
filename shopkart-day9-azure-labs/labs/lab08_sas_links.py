"""
LAB 8 - Sharing private blobs safely with SAS links
===================================================
Curriculum topic : "Accessing Blob storage through ... SAS links"

SAS = Shared Access Signature = a URL with a SIGNED "permission slip" attached:
   https://<account>.blob.core.windows.net/invoices/inv.pdf?sp=r&se=2026-11-17T10:15Z&sig=...
                                                            |     |                     |
                                                   permissions  expiry          signature (HMAC with
                                                                                 the account key)
Anyone holding the URL can do ONLY what sp= allows, ONLY until se= expires.
Change one character of the URL -> signature breaks -> 403.

ShopKart scenarios tested here (every one runs against Azurite or Azure):
  S1  Customer clicks "Download invoice" -> READ-only blob SAS, 15 minutes
  S2  Vendor app uploads product photos  -> CREATE+WRITE container SAS (cannot read/list!)
  S3  Link expired                       -> 403
  S4  Tampered link (customer edits blob name to see someone else's invoice) -> 403
  S5  Leaked link must be killed NOW     -> stored access policy, revoke = delete policy
  S6  (Azure only) User-delegation SAS   -> signed with Entra ID, no account key at all

Run:  python labs/lab08_sas_links.py
"""
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from azure.core.exceptions import HttpResponseError  # noqa: E402
from azure.storage.blob import (  # noqa: E402
    AccessPolicy, BlobClient, BlobSasPermissions, ContainerClient, ContainerSasPermissions,
    ContentSettings, generate_blob_sas, generate_container_sas,
)

from common import config  # noqa: E402
from common.clients import blob_service_client  # noqa: E402
from common.pretty import banner, step, info, ok, warn, fail  # noqa: E402


def now():
    return datetime.now(timezone.utc)


def http_get(url: str) -> tuple[int, bytes]:
    """Plain HTTP GET - exactly what a customer's browser does with the link."""
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def account_key(service) -> str:
    key = getattr(service.credential, "account_key", None)
    if not key:
        print("SAS signing needs the account KEY (connection string with AccountKey=...)."
              " Or use the user-delegation SAS (S6) with Entra ID.")
        sys.exit(1)
    return key


def prepare(service):
    for name in ("invoices", "vendor-uploads"):
        try:
            service.create_container(name)
        except HttpResponseError:
            pass
    for cust, inv in (("CUST-001", "INV-ORD-2026-0001.pdf"), ("CUST-002", "INV-ORD-2026-0004.pdf")):
        service.get_blob_client("invoices", f"customers/{cust}/{inv}").upload_blob(
            (config.ASSETS_DIR / "invoice_technova.pdf").read_bytes(), overwrite=True,
            content_settings=ContentSettings(content_type="application/pdf"))


# --------------------------------------------------------------------- S1 --
def s1_customer_download(service, key):
    step("S1) Ananya clicks 'Download invoice' -> backend returns a 15-minute READ-ONLY link")
    blob_name = "customers/CUST-001/INV-ORD-2026-0001.pdf"
    sas = generate_blob_sas(
        account_name=service.account_name,
        container_name="invoices",
        blob_name=blob_name,
        account_key=key,
        permission=BlobSasPermissions(read=True),          # sp=r
        start=now() - timedelta(minutes=5),                 # clock-skew safety
        expiry=now() + timedelta(minutes=15),               # se=...
        content_disposition="attachment; filename=ShopKart_Invoice_ORD-2026-0001.pdf",
    )
    url = f"{service.url.rstrip('/')}/invoices/{blob_name}?{sas}"
    info(f"SAS URL: {url[:110]}...")
    info("Query string parts: " + ", ".join(p.split("=")[0] for p in sas.split("&")))
    status, body = http_get(url)
    (ok if status == 200 else fail)(f"Browser GET -> HTTP {status}, {len(body)} bytes, starts with {body[:5]!r}")

    step("    Same link, but try to OVERWRITE the invoice with it")
    try:
        BlobClient.from_blob_url(url).upload_blob(b"fake invoice", overwrite=True)
        fail("Upload worked?! permission should be read-only")
    except HttpResponseError as e:
        ok(f"Upload blocked -> HTTP {e.status_code} ({e.error_code}). Read-only means read-only.")
    return url


# --------------------------------------------------------------------- S2 --
def s2_vendor_upload(service, key):
    step("S2) Vendor 'TechNova' gets an UPLOAD-ONLY link to 'vendor-uploads' for 1 hour")
    sas = generate_container_sas(
        account_name=service.account_name,
        container_name="vendor-uploads",
        account_key=key,
        permission=ContainerSasPermissions(create=True, write=True),   # NO read, NO list, NO delete
        expiry=now() + timedelta(hours=1),
    )
    container_url = f"{service.url.rstrip('/')}/vendor-uploads?{sas}"
    vendor_side = ContainerClient.from_container_url(container_url)    # this code runs at the VENDOR
    vendor_side.upload_blob("technova/ELEC-1001-front.png",
                            (config.ASSETS_DIR / "product_images" / "ELEC-1001.png").read_bytes(),
                            overwrite=True, content_settings=ContentSettings(content_type="image/png"))
    ok("Vendor uploaded technova/ELEC-1001-front.png using only the SAS URL (no keys shared)")
    try:
        list(vendor_side.list_blobs())
        fail("Vendor could list other vendors' files!")
    except HttpResponseError as e:
        ok(f"Vendor tried to LIST the container -> HTTP {e.status_code}. Cannot see competitors' files.")


# --------------------------------------------------------------------- S3 --
def s3_expired(service, key):
    step("S3) Customer opens the invoice email 2 days later -> link expired")
    blob_name = "customers/CUST-001/INV-ORD-2026-0001.pdf"
    sas = generate_blob_sas(service.account_name, "invoices", blob_name, account_key=key,
                            permission=BlobSasPermissions(read=True),
                            start=now() - timedelta(hours=2), expiry=now() - timedelta(minutes=1))
    status, _ = http_get(f"{service.url.rstrip('/')}/invoices/{blob_name}?{sas}")
    (ok if status == 403 else fail)(f"HTTP {status} -> UI should say 'Link expired, click to generate a new one'")


# --------------------------------------------------------------------- S4 --
def s4_tampered(s1_url):
    step("S4) Curious customer edits the URL: CUST-001 -> CUST-002 to read Rahul's invoice")
    hacked = s1_url.replace("CUST-001", "CUST-002").replace("ORD-2026-0001", "ORD-2026-0004")
    status, _ = http_get(hacked)
    (ok if status == 403 else fail)(f"HTTP {status} -> signature covers the blob path; editing it breaks the sig")


# --------------------------------------------------------------------- S5 --
def s5_revocable(service, key):
    step("S5) Stored access policy: a link we can REVOKE before it expires")
    container = service.get_container_client("invoices")
    container.set_container_access_policy(signed_identifiers={
        "finance-readonly": AccessPolicy(permission=ContainerSasPermissions(read=True, list=True),
                                         expiry=now() + timedelta(days=7), start=now() - timedelta(minutes=5)),
    })
    ok("policy 'finance-readonly' created on container 'invoices' (read+list, 7 days)")
    sas = generate_container_sas(service.account_name, "invoices", account_key=key, policy_id="finance-readonly")
    finance = ContainerClient.from_container_url(f"{service.url.rstrip('/')}/invoices?{sas}")
    names = [b.name for b in finance.list_blobs()]
    ok(f"Auditor's link works: sees {len(names)} invoice files")

    warn("Auditor's laptop is stolen! Revoke by removing the policy:")
    container.set_container_access_policy(signed_identifiers={})
    try:
        list(finance.list_blobs())
        warn("Still works - on Azure, policy changes can take up to 30 seconds to apply.")
    except HttpResponseError as e:
        ok(f"Same link now -> HTTP {e.status_code}. Revoked without rotating the account key.")


# --------------------------------------------------------------------- S6 --
def s6_user_delegation():
    step("S6) User-delegation SAS (best practice on Azure - no account key involved)")
    if config.IS_AZURITE or not config.flag("USE_ENTRA_ID"):
        warn("Skipped (needs Azure + USE_ENTRA_ID=true + 'Storage Blob Data Contributor' role). The code:")
        print('''
      from azure.identity import DefaultAzureCredential
      svc = BlobServiceClient(account_url, credential=DefaultAzureCredential())
      udk = svc.get_user_delegation_key(now(), now() + timedelta(hours=1))
      sas = generate_blob_sas(svc.account_name, "invoices", blob_name,
                              user_delegation_key=udk,
                              permission=BlobSasPermissions(read=True),
                              expiry=now() + timedelta(minutes=15))''')
        return
    from azure.storage.blob import BlobServiceClient
    from azure.identity import DefaultAzureCredential
    svc = BlobServiceClient(config.require("STORAGE_ACCOUNT_URL"), credential=DefaultAzureCredential())
    udk = svc.get_user_delegation_key(now() - timedelta(minutes=5), now() + timedelta(hours=1))
    blob_name = "customers/CUST-001/INV-ORD-2026-0001.pdf"
    sas = generate_blob_sas(svc.account_name, "invoices", blob_name, user_delegation_key=udk,
                            permission=BlobSasPermissions(read=True), expiry=now() + timedelta(minutes=15))
    status, _ = http_get(f"{svc.url.rstrip('/')}/invoices/{blob_name}?{sas}")
    (ok if status == 200 else fail)(f"User-delegation SAS GET -> HTTP {status}")


def main():
    banner("LAB 8 - SAS links (ShopKart)")
    service = blob_service_client()
    key = account_key(service)
    prepare(service)
    url = s1_customer_download(service, key)
    s2_vendor_upload(service, key)
    s3_expired(service, key)
    s4_tampered(url)
    s5_revocable(service, key)
    s6_user_delegation()
    step("Golden rules")
    for r in ["Shortest expiry that works (minutes, not months)", "Least permission (r for download, cw for upload)",
              "Generate SAS on the BACKEND; never ship the account key to a browser/mobile app",
              "Prefer user-delegation SAS; use stored access policies when you need revoke",
              "HTTPS only in production (protocol='https')"]:
        info(f"* {r}")
    banner("LAB 8 complete")


if __name__ == "__main__":
    main()
