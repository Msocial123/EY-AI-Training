# Day 10 – ShopEase Daily Sales Data Pipeline

A complete, beginner-friendly **data pipeline** for an ecommerce company, built for Day 10
(Data Pipelines) of the corporate training program.

Every night ShopEase's website exports the day's orders as a CSV file, and suppliers send
their invoices as PDF files. This project automatically:

1. **Extracts** the raw orders (CSV) and reads supplier invoices (PDF, using PyMuPDF).
2. **Transforms** the data – removes duplicates, rejects bad rows with a reason,
   standardises text, calculates GST and totals, builds a daily category summary,
   and checks every invoice (subtotal + tax = total).
3. **Loads** the results into a SQLite "warehouse" and writes a JSON run report.
4. Optionally **uploads** the reports to Azure Blob Storage.
5. Runs **automatically on a schedule** (Python `schedule` library).
6. Can run as a **two-step Azure Machine Learning pipeline** (Azure ML SDK v2).

## Technologies used

| Purpose | Technology |
|---|---|
| Language | Python 3.10+ |
| Data processing | pandas |
| PDF text extraction | PyMuPDF (`pymupdf`) |
| Storage / warehouse | SQLite (built into Python) |
| Scheduling | `schedule` library |
| Cloud storage (optional) | Azure Blob Storage SDK (`azure-storage-blob`) |
| Cloud pipelines (optional) | Azure ML SDK v2 (`azure-ai-ml`, `azure-identity`) |
| Testing | pytest |

## Prerequisites

- Python 3.10 or newer (`python --version`)
- VS Code (recommended)
- Optional: an Azure Storage account (for Blob upload) and an Azure ML workspace with a
  compute cluster (for the Azure ML pipeline)

## Installation

```bash
cd Day10_Practical_Project
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

## How to run

Always run commands **from the project folder** (the folder that contains `pipeline/`).

```bash
# 1. Create the sample invoice PDFs (only needed once)
python scripts/generate_sample_invoices.py

# 2. Run the full pipeline (Extract -> Transform -> Load)
python -m pipeline.run_pipeline

# 3. Run the unit tests
python -m pytest -v

# 4. Run the pipeline on a schedule
python -m scheduler.schedule_runner --demo      # every 10 seconds (classroom demo)
python -m scheduler.schedule_runner             # every day at 02:00 (settings.json)

# 5. Run one stage at a time (this is exactly what Azure ML does)
python -m pipeline.run_pipeline --stage transform --input data/raw --output data/staging
python -m pipeline.run_pipeline --stage load --input data/staging --output data/processed

# 6. Azure ML pipeline
python -m azureml.aml_pipeline --dry-run        # build and print, no Azure needed
python -m azureml.aml_pipeline                  # submit (needs az login + env variables)
```

### Optional: Azure Blob upload

```bash
# Windows PowerShell:  $env:AZURE_STORAGE_CONNECTION_STRING="<your connection string>"
export AZURE_STORAGE_CONNECTION_STRING="<your connection string>"
python -m pipeline.run_pipeline
```

If the variable is not set, the upload step is skipped and the pipeline still succeeds.

### Optional: Azure ML submission

```bash
az login
export AZURE_SUBSCRIPTION_ID="<subscription id>"
export AZURE_RESOURCE_GROUP="<resource group>"
export AZUREML_WORKSPACE="<workspace name>"
export AZUREML_COMPUTE="<compute cluster name>"
python -m azureml.aml_pipeline
```

## Project structure

```
Day10_Practical_Project/
├── README.md
├── requirements.txt
├── .gitignore                 # keeps generated data and logs out of Git
├── .amlignore                 # keeps data and logs out of the Azure ML code upload
├── config/
│   └── settings.json          # all paths and business rules in one place
├── data/
│   └── raw/
│       ├── orders_2026-11-18.csv      # sample (messy) order export
│       └── invoices/                  # sample supplier invoice PDFs (generated)
├── pipeline/
│   ├── __init__.py
│   ├── config.py              # load_settings(), resolve_path()
│   ├── logger.py              # get_logger()
│   ├── extract.py             # extract_orders(), parse_invoice_text(), extract_invoices()
│   ├── transform.py           # clean_orders(), add_order_totals(),
│   │                          # build_category_summary(), validate_invoices()
│   ├── load.py                # load_to_sqlite(), write_run_report()
│   ├── storage.py             # upload_to_blob()  (optional Azure Blob)
│   └── run_pipeline.py        # orchestrator: run_transform_stage(), run_load_stage(),
│                              # parse_args(), main()
├── scheduler/
│   ├── __init__.py
│   └── schedule_runner.py     # pipeline_job(), start_scheduler()
├── azureml/
│   ├── __init__.py
│   ├── environment.yml        # packages the cloud machine needs
│   └── aml_pipeline.py        # two-step Azure ML pipeline
├── scripts/
│   └── generate_sample_invoices.py   # create_invoice_pdf()
└── tests/
    └── test_pipeline.py       # 4 pytest unit tests
```

Created when the pipeline runs (ignored by Git):

```
data/staging/      orders_clean.csv, rejected_orders.csv, category_summary.csv, invoices.csv
data/processed/    category_summary.csv, run_report.json
data/warehouse/    shopease.db  (tables: fact_orders, rejected_orders,
                                  daily_category_sales, supplier_invoices)
logs/              pipeline_YYYY-MM-DD.log
```

## Application functionality

| Command | What it does |
|---|---|
| `python -m pipeline.run_pipeline` | Full run with paths from `settings.json` |
| `--stage transform --input X --output Y` | Extract + Transform only; writes staged CSVs to Y |
| `--stage load --input Y --output Z` | Load staged CSVs from Y into `Z/shopease.db` |
| `python -m scheduler.schedule_runner` | Runs the full pipeline daily at `schedule_time` |
| `python -m azureml.aml_pipeline` | Submits the 2-step pipeline to Azure ML |

Exit codes: `0` = success, `1` = failure (schedulers and CI tools read this).

## Sample input and expected output

**Input:** `data/raw/orders_2026-11-18.csv` has 14 rows, including deliberate problems:
one duplicate (ORD-1005), a missing customer (ORD-1003), quantity 0 (ORD-1004),
price `abc` (ORD-1007), status `RETURNED` (ORD-1010) and a wrong date format (ORD-1011).
Invoice `INV-2026-1103` has a wrong total (30,500 + 5,490 ≠ 36,500).

**Console output of `python -m pipeline.run_pipeline`:**

```
INFO    | Pipeline started | stage=all | input=.../data/raw
INFO    | Extracted 14 raw order rows
INFO    | Extracted 3 invoices from PDF files
INFO    | Clean orders: 8 | Rejected orders: 5
WARNING | 1 invoice(s) failed the subtotal + tax = total check
INFO    | Staged files written to .../data/staging
INFO    | Loaded tables: {'fact_orders': 8, 'rejected_orders': 5, 'daily_category_sales': 5, 'supplier_invoices': 3}
INFO    | Pipeline SUCCESS in 0.07 s | report: .../data/processed/run_report.json
INFO    | AZURE_STORAGE_CONNECTION_STRING not set - skipping Blob upload
```

**`data/processed/category_summary.csv`:**

```
sales_date,category,orders,units_sold,revenue_incl_gst
2026-11-17,Electronics,1,1,29498.82
2026-11-17,Fashion,2,5,5895.28
2026-11-18,Electronics,1,1,64898.82
2026-11-18,Home & Kitchen,2,6,5184.92
2026-11-18,Fashion,1,1,2948.82
```

**`data/processed/run_report.json`:**

```json
{
  "pipeline": "shopease_daily_sales",
  "status": "SUCCESS",
  "started_at": "2026-11-18T09:15:47",
  "finished_at": "2026-11-18T09:15:47",
  "row_counts": {"fact_orders": 8, "rejected_orders": 5,
                 "daily_category_sales": 5, "supplier_invoices": 3}
}
```

**Query the warehouse:**

```bash
python -c "import sqlite3; c=sqlite3.connect('data/warehouse/shopease.db'); print(c.execute('select order_id, reject_reason from rejected_orders').fetchall())"
```

## Notes

- The Azure ML SDK prints some "experimental class" warnings on import. They are harmless.
- The pipeline is **idempotent**: running it twice gives the same result, because each run
  replaces the tables (`if_exists="replace"`).
