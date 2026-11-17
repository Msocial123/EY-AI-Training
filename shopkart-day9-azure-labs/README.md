# ShopKart – Day 9 Azure Labs
### Unstructured / Semi-Structured Data – Part 2

Hands-on labs for freshers. Every lab is built around **ShopKart**, a fictional Indian e-commerce company, so each concept answers a real business question.

| # | Lab file | Curriculum topic | ShopKart story | Needs Azure? |
|---|----------|------------------|----------------|--------------|
| 1 | `lab01_cosmos_setup.py` | Using Azure Portal for Cosmos DB | Create DB, containers, load catalogue & orders | No (emulator) |
| 2 | `lab02_cosmos_sql_queries.py` | Querying with SQL API | Search, filters, low-stock alerts, My Orders, pagination, PATCH, ETag | No (emulator) |
| 3 | `lab03_consistency_levels.py` | Consistency Levels | Cart read-your-writes across servers with session tokens | No (emulator)* |
| 4 | `lab04_cosmos_security.py` | Basic Security & Access Control | Read-only key, Entra ID + RBAC, secrets hygiene | Partly** |
| 5 | `lab05_ocr_read.py` | Introduction to OCR | Product label MRP check, handwritten return note | Optional (offline mode) |
| 6 | `lab06_document_intelligence.py` | Azure Doc Intelligence | Supplier invoice → PO match, expense receipt | Optional (offline mode) |
| 7 | `lab07_blob_storage_sdk.py` | Blob storage through SDK | Upload/list/download product images, tiers | No (Azurite) |
| 8 | `lab08_sas_links.py` | SAS links | Invoice download link, vendor upload link, expiry, tamper, revoke | No (Azurite) |
| 9 | `lab09_capstone_invoice_pipeline.py` | **All topics** | Vendor upload → AI extraction → Cosmos → finance SAS link | No |
| 10 | `lab10_shopkart_api.py` | **Bonus** | Same code inside a Flask REST API | No |

\* Emulator has one replica, so all levels behave the same – the code is identical on Azure.
\** Emulator does not enforce keys/RBAC; the 403 demo needs a real Cosmos DB account.

---

## 1. Setup (15 minutes)

**Prerequisites:** Python 3.10+, VS Code, Docker Desktop, Git.

```bash
git clone <this-repo-url>
cd shopkart-day9-azure-labs

python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
```

### Start the local emulators (no Azure subscription needed)

```bash
docker compose up -d
```

* Cosmos DB emulator → API `http://localhost:8081`, Data Explorer `http://localhost:1234`
* Azurite (Blob) → `http://127.0.0.1:10000`

Wait ~30 seconds for Cosmos to start (`curl http://localhost:8080/ready`).

> **No Docker?** Azurite also installs with npm: `npm i -g azurite` then `azurite-blob --location .azurite`.

## 2. Run the labs in order

```bash
python labs/lab01_cosmos_setup.py
python labs/lab02_cosmos_sql_queries.py
python labs/lab03_consistency_levels.py
python labs/lab04_cosmos_security.py
python labs/lab05_ocr_read.py
python labs/lab06_document_intelligence.py
python labs/lab07_blob_storage_sdk.py
python labs/lab08_sas_links.py
python labs/lab09_capstone_invoice_pipeline.py
python labs/lab10_shopkart_api.py      # then open http://127.0.0.1:5000/api/products?category=Books
```

Check everything without any cloud/emulator: `python tests/test_labs_offline.py`

## 3. Switching to real Azure

| Service | Create in Portal | Copy into `.env` | Free option |
|---------|------------------|------------------|-------------|
| Cosmos DB for NoSQL | Create a resource → Azure Cosmos DB → **NoSQL** | URI → `COSMOS_ENDPOINT`, Primary key → `COSMOS_KEY`, Read-only key → `COSMOS_READONLY_KEY` | Free tier (1000 RU/s + 25 GB, one per subscription) or Serverless |
| Storage account | Create a resource → Storage account (Standard, LRS) | Access keys → Connection string → `STORAGE_CONNECTION_STRING` | Pay-per-use, a few rupees for these labs |
| Azure AI Vision *(optional)* | Create a resource → Computer Vision | Keys and Endpoint → `VISION_ENDPOINT`, `VISION_KEY` | F0 tier |
| Document Intelligence | Create a resource → Document Intelligence | Keys and Endpoint → `DOCINTEL_ENDPOINT`, `DOCINTEL_KEY` | F0 tier |

Free-tier limits and regions change – check the pricing page before the session.

> **OCR engine choice:** Image Analysis 4.0 (Azure AI Vision) is scheduled to retire on **25 Sep 2028**, and Microsoft's migration guidance sends OCR workloads to Document Intelligence's `prebuilt-read` model. Lab 5 therefore uses Document Intelligence when its keys are set, falls back to Vision, then to offline samples. One Document Intelligence resource covers labs 5, 6 and 9.

## 4. Project structure

```
common/           config (.env), Azure client factory, pretty printing
data/             products.json (20 items), orders.json (15 orders)
assets/           product_label.png, return_note.png, receipt_store.png, invoice_technova.pdf, product_images/
labs/             lab01 ... lab10
sample_outputs/   recorded-shape AI responses used in OFFLINE mode
exercises/        practice tasks + solutions
tests/            offline smoke tests (fake Cosmos)
tools/            make_sample_assets.py (regenerates data and images)
docker-compose.yml  Cosmos DB emulator + Azurite
```

## 5. Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `CONFIG ERROR 'COSMOS_KEY' is not set` | No `.env` | `cp .env.example .env` |
| `ServiceRequestError ... 8081` | Emulator not running / still starting | `docker compose up -d`, wait 30 s |
| `CosmosResourceNotFoundError` on read | Wrong partition key value | Pass the item's `category` / `customerId` |
| `Cross partition query is required but disabled` | Query without partition key | add `enable_cross_partition_query=True` or pass `partition_key` |
| `AuthorizationPermissionMismatch` (403) on blob | SAS lacks that permission | check `sp=` in the SAS |
| `AuthenticationFailed` (403) on blob | SAS expired or URL edited | generate a new SAS |
| `401 Access denied` from AI services | Wrong key or key/endpoint from different resources | copy both from the same resource's *Keys and Endpoint* page |

All data is fictional and for training only.
