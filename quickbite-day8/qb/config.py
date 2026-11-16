"""QuickBite shared config: one place that knows how to connect to Cosmos DB.
Every live-coding script imports from here, so the scripts stay short."""
import os
from pathlib import Path
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, PartitionKey

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Public, documented key of the LOCAL emulator - not a secret, never valid in Azure.
# Windows emulator = https://localhost:8081/   ·   Docker (Linux vNext) emulator = http://localhost:8081/
_EMULATOR_URL = os.getenv("COSMOS_EMULATOR_URL", "http://localhost:8081/").strip()
_EMULATOR_KEY = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="

# Each fresher can use their own database on a SHARED account, e.g. COSMOS_DATABASE=QuickBite_ravi
DB_NAME = os.getenv("COSMOS_DATABASE", "QuickBiteDB_prem").strip() or "QuickBiteDB"
# Provisioned accounts: ONE shared RU/s pool for the whole database (1,000 = stays inside the free tier)
SHARED_RU = int(os.getenv("COSMOS_DB_THROUGHPUT", "1000"))


def _flag(name):
    return os.getenv(name, "false").strip().lower() in ("1", "true", "yes")


def get_client(consistency_level=None):
    kw = {"consistency_level": consistency_level} if consistency_level else {}
    if _flag("COSMOS_EMULATOR"):
        return CosmosClient(_EMULATOR_URL, credential=_EMULATOR_KEY, connection_verify=False, **kw)
    endpoint, key = os.getenv("COSMOS_ENDPOINT", ""), os.getenv("COSMOS_KEY", "")
    if not endpoint or endpoint.startswith("https://<"):
        raise SystemExit("Set COSMOS_ENDPOINT and COSMOS_KEY in .env (copy .env.example)")
    return CosmosClient(endpoint, credential=key, **kw)


def get_container(name, pk_path, client=None):
    """Create-if-missing and return a container.
    Serverless: no throughput settings at all.
    Provisioned: containers share the database's RU/s pool, so 7 lab containers still cost
    1,000 RU/s in total (free tier) instead of 7 x 400 = 2,800 RU/s."""
    client = client or get_client()
    if _flag("COSMOS_SERVERLESS") or _flag("COSMOS_EMULATOR"):
        db = client.create_database_if_not_exists(id=DB_NAME)
    else:
        db = client.create_database_if_not_exists(id=DB_NAME, offer_throughput=SHARED_RU)
    return db.create_container_if_not_exists(id=name, partition_key=PartitionKey(path=pk_path))


def ru(container):
    """RU charge of the LAST point operation (read/create/upsert/replace/patch/delete)."""
    h = container.client_connection.last_response_headers or {}
    return float(h.get("x-ms-request-charge", 0) or 0)


def query(container, sql, params=None, pk=None):
    """Run a query; return (items, total RU across every page / partition)."""
    charges = {}

    def hook(headers, _):
        charges[headers.get("x-ms-activity-id") or len(charges)] = float(headers.get("x-ms-request-charge", 0) or 0)

    kw = {"query": sql, "parameters": params or [], "response_hook": hook}
    if pk is None:
        kw["enable_cross_partition_query"] = True
    else:
        kw["partition_key"] = pk
    items = list(container.query_items(**kw))
    return items, round(sum(charges.values()) or ru(container), 2)


def on_emulator():
    return _flag("COSMOS_EMULATOR")


def title(t):
    print("\n" + "=" * 64 + f"\n  {t}\n" + "=" * 64)
