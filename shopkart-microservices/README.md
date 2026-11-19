# 🛒 ShopKart Microservices — Day 12 Hands-on Project

**Building Microservices with FastAPI, Flask & Introduction to Azure**

A small but realistic e-commerce backend split into microservices. Everything runs on your laptop
**without Azure**. When you are ready, flip one setting and the same code uses real Azure services.

## What's inside

| Folder | What it is | Tech | Port |
|---|---|---|---|
| `product_service/` | Product catalog (list, search, add, update, delete) | FastAPI | 8001 |
| `order_service/` | Place / view / cancel orders, sends `OrderPlaced` event | FastAPI | 8002 |
| `inventory_service/` | Warehouse stock (reserve, restock) | **Flask** | 8003 |
| `workers/order_worker.py` | Background worker: reads queue → reserves stock → confirms order | Python | – |
| `gateway/mini_gateway.py` | Mini load balancer + API gateway (round robin, failover, path routing) | FastAPI | 8000 |
| `common/` | Settings, queue helper (Local / Storage Queue / Service Bus), Azure clients | – | – |
| `azure_demos/` | Blob upload, Storage Queue, Service Bus queue + topic, identity check | Azure SDK | – |
| `infra/` | Azure CLI scripts: resource group, storage, service bus, load balancer, app gateway | az CLI | – |
| `tests/` | 44 pytest tests (schemas, FastAPI, Flask, queue, gateway, worker) | pytest | – |

## Architecture

```
                     ┌──────────────────────────┐
  Browser / Postman ─▶  Mini Gateway  :8000     │  /api/products/* ─▶ product pool (8001, 8011)  round robin
                     │  (Load Balancer + AppGW) │  /api/orders/*   ─▶ order pool   (8002)
                     └──────────────────────────┘  /api/inventory/*─▶ inventory    (8003)

  Order Service ──HTTP──▶ Product Service      (get real price)
  Order Service ──send──▶ QUEUE ──receive──▶ Order Worker ──HTTP──▶ Inventory (Flask)
                                                    └──HTTP──▶ Order Service (CONFIRMED / FAILED)
```

## 1. Setup (one time)

Needs **Python 3.10+**.

```bash
git clone <this-repo-url> shopkart-microservices
cd shopkart-microservices

python -m venv .venv
# Windows:      .venv\Scripts\activate
# Mac / Linux:  source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
```

## 2. Run the tests first (proves your setup works)

```bash
pytest -v
```
Expected: `44 passed`.

## 3. Start the services (one terminal each, venv activated in each)

```bash
python run.py product                          # :8001
python run.py product --port 8011 --name product-2   # second copy for load balancing
python run.py inventory                        # :8003 (Flask)
python run.py order                            # :8002
python run.py gateway                          # :8000
python run.py worker                           # background worker
```

Open Swagger UI: http://127.0.0.1:8001/docs and http://127.0.0.1:8002/docs

## 4. Try the full order flow

```bash
curl -X POST http://127.0.0.1:8000/api/orders -H "Content-Type: application/json" -d @sample_data/order.json
curl http://127.0.0.1:8000/api/orders/1        # PLACED -> CONFIRMED after the worker runs
python -m gateway.hit_gateway 10               # see round robin
```

Ready-made request bodies for curl live in `sample_data/` (`new_product.json`, `bad_product.json`,
`patch_price.json`, `order.json`, `order_cod.json`, `order_out_of_stock.json`, `bad_order.json`,
`reserve_ok.json`, `reserve_too_many.json`, `restock.json`). Send them with `-d @sample_data/<file>.json`.
On Windows PowerShell type `curl.exe` instead of `curl`.

## 5. Use real Azure (optional)

1. In **Azure Cloud Shell** run `infra/01_resource_group_and_storage.sh` and `infra/02_service_bus.sh`
2. Locally: `az login`
3. Put the names printed by the scripts into `.env` and set `QUEUE_BACKEND=storage_queue` or `service_bus`
4. Run `python -m azure_demos.check_identity`, then the other `azure_demos`
5. **Always** run `infra/99_cleanup.sh` at the end of the day

**No Azure subscription?** Use the Azurite emulator for Blob + Queue:
`npm install -g azurite` → `azurite --silent --location .azurite` → in `.env` set
`AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true`.

## 6. Practice tasks (do these after class)

1. **Easy** – Add `GET /products/{product_id}/price` that returns only `name`, `price`, `mrp`, `discount_percent`.
2. **Easy** – Add a `min_rating` query parameter to `GET /products` (filter by seller rating).
3. **Medium** – Add a `coupon_code` field to `OrderCreate` (`SAVE10` = 10% off, max Rs 500) and test it.
4. **Medium** – Add `GET /inventory/low-stock?threshold=5` to the Flask service + a pytest test.
5. **Medium** – Make the worker publish an `OrderConfirmed` message to a second queue named `notifications`.
6. **Stretch** – Add a third route `/api/reviews/*` to the gateway for a new Flask review service.

## Common errors

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'product_service'` | Run commands from the project root folder |
| `Address already in use` / `[Errno 98]` / `10048` | Another service uses that port. Stop it (Ctrl+C) or use `--port` |
| `503 Product service is down` when placing an order | Start the product service first |
| `AuthorizationPermissionMismatch` from Azure | Role assignment is missing or still propagating (wait 5 min) |
| `DefaultAzureCredential failed to retrieve a token` | Run `az login` (and `az account set --subscription <id>`) |
