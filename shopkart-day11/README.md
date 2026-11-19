# ShopKart — Day 11: Python Configs, Validation & Microservices Basics

Hands-on code for an 8-hour training day. Every example uses **ShopKart**, a pretend
Indian e-commerce company (products, carts, coupons, GST, orders, payments).

## Setup (one time)

```bash
# Mac / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Python 3.9 or newer.

## What is inside

| Folder | Topic | Run |
|---|---|---|
| `module1_configs/` | JSON, YAML, INI, `.env` secrets, layered config | `python m1_01_json_basics.py` … `m1_04` |
| `module2_pydantic/` | Models, type conversion, Field rules, validators, nested models, serialization, validating config | `python m2_01_models_basics.py` … `m2_04` |
| `module3_logging_errors/` | Logging levels, file + rotating logs, custom exceptions, retry with backoff | `python m3_01_logging_basics.py` … `m3_04` |
| `module4_rest_microservices/` | REST verbs + status codes, two microservices calling each other | see below |
| `module5_flask/` | Flask routes, HTML templates + forms, JSON API with Pydantic | `python m5_01_hello_flask.py` … `m5_03` |
| `capstone/` | A properly structured project: config + validation + logging + errors + REST API + tests | `python run.py`, `python -m pytest -v` |
| `labs/` | Practice tasks with solutions | `python lab1_flash_sale_solution.py` … |

**Run every script from inside its own folder** (`cd module1_configs` first).

## Ports used

| App | Port |
|---|---|
| Catalog microservice | 5001 |
| Order microservice | 5002 |
| Module 5 Flask apps (one at a time) | 5005 |
| Lab 4 Reviews API | 5006 |
| Capstone ShopKart API | 8000 |

We avoid port 5000 because macOS uses it for AirPlay Receiver.

## Module 4: microservices demo

```bash
# Terminal 1
cd module4_rest_microservices && python catalog_service.py
# Terminal 2
cd module4_rest_microservices && python order_service.py
# Terminal 3
cd module4_rest_microservices && python m4_01_rest_client.py
python m4_02_microservices_demo.py
```

## Capstone project structure

```
capstone/
├── config/              settings.yaml (+ settings.prod.yaml overrides)
├── data/products.json   starting catalogue
├── shopkart/
│   ├── __init__.py      create_app(): wires everything together
│   ├── config.py        YAML -> env overrides -> Pydantic Settings
│   ├── logging_setup.py console + rotating file logs
│   ├── exceptions.py    business errors with HTTP status codes
│   ├── schemas.py       Pydantic request models (the API contract)
│   ├── repository.py    data access (swap for a DB later)
│   ├── services.py      business rules: GST, coupons, shipping, stock
│   └── routes.py        thin HTTP layer (Flask Blueprint, /api/v1)
├── tests/               pytest unit + API tests
├── api_requests.http    ready-made requests for VS Code REST Client
└── run.py
```

## Never commit secrets

`.env` is in `.gitignore`. Only `.env.example` (fake values) goes to Git.
