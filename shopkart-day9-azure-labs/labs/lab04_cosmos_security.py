"""
LAB 4 - Basic security and access control for Cosmos DB
=======================================================
Curriculum topic : "Basic Security and Access Control"

ShopKart has 3 kinds of apps touching the database:
  * Storefront API        -> reads products, writes orders     (read-write)
  * Analytics dashboard   -> only reads                         (read-only)
  * Interns' laptops      -> should NOT hold master keys at all (Entra ID + RBAC)

Ladder of security (bottom = weakest):
  4. Microsoft Entra ID + RBAC role per app, local keys DISABLED   <- production goal
  3. Read-only key for apps that only read
  2. Primary key stored in .env / Key Vault, rotated regularly
  1. Primary key hard-coded in code and pushed to GitHub           <- breach waiting to happen

Run:  python labs/lab04_cosmos_security.py
Needs (for the read-only test): COSMOS_READONLY_KEY in .env
Needs (for the Entra ID test) : USE_ENTRA_ID=true, `az login`, and a role assignment
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from azure.cosmos import CosmosClient, exceptions  # noqa: E402

from common import config  # noqa: E402
from common.pretty import banner, step, info, ok, warn, fail  # noqa: E402

BAD_EXAMPLE = '''
    # NEVER DO THIS - the key ends up in Git history forever
    client = CosmosClient("https://shopkart.documents.azure.com:443/",
                          "C2y6yDjf5/R+ob0N8A7Cgv30VRDJ...==")
'''

GOOD_EXAMPLE = '''
    # DO THIS - key comes from environment / Key Vault, .env is in .gitignore
    client = CosmosClient(os.environ["COSMOS_ENDPOINT"], os.environ["COSMOS_KEY"])

    # BEST - no key at all, identity-based access
    client = CosmosClient(os.environ["COSMOS_ENDPOINT"], DefaultAzureCredential())
'''

RBAC_COMMANDS = r'''
# 1) Who am I? (copy the "id" value = your principal / object id)
az ad signed-in-user show --query id -o tsv

# 2) Built-in DATA-plane roles for Cosmos DB (NoSQL):
#    00000000-0000-0000-0000-000000000001 = Cosmos DB Built-in Data Reader
#    00000000-0000-0000-0000-000000000002 = Cosmos DB Built-in Data Contributor

# 3) Give the analytics dashboard identity READ-ONLY data access to ONE database
az cosmosdb sql role assignment create \
   --account-name <cosmos-account> --resource-group <rg> \
   --role-definition-id 00000000-0000-0000-0000-000000000001 \
   --principal-id <object-id> \
   --scope "/dbs/shopkart"

# 4) Production hardening: turn OFF key-based access entirely
az resource update --resource-type "Microsoft.DocumentDB/databaseAccounts" \
   --name <cosmos-account> --resource-group <rg> \
   --set properties.disableLocalAuth=true
'''


def part1_secrets_hygiene():
    step("1) Where should the key live?")
    info("BAD:" + BAD_EXAMPLE)
    info("GOOD:" + GOOD_EXAMPLE)
    gitignore = (config.ROOT / ".gitignore")
    if gitignore.exists() and ".env" in gitignore.read_text():
        ok(".env is listed in .gitignore - your keys will not be committed.")
    else:
        fail(".env is NOT in .gitignore - fix this before your first commit!")


def part2_read_only_key():
    step("2) Analytics dashboard uses the READ-ONLY key")
    ro_key = config.get("COSMOS_READONLY_KEY")
    if not ro_key:
        warn("COSMOS_READONLY_KEY not set. Portal > Cosmos account > Keys > 'Read-only Keys' tab.")
        return
    client = CosmosClient(config.COSMOS_ENDPOINT, credential=ro_key,
                          connection_verify=not config.flag("COSMOS_DISABLE_SSL_VERIFY"))
    products = client.get_database_client(config.COSMOS_DATABASE).get_container_client("products")

    count = list(products.query_items("SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True))[0]
    ok(f"READ works with read-only key: {count} products")

    try:
        products.create_item({"id": f"HACK-{uuid.uuid4().hex[:4]}", "category": "Electronics",
                              "name": "Fake product", "price": 1})
        if config.IS_COSMOS_EMULATOR:
            warn("WRITE succeeded because the emulator does NOT enforce keys/RBAC. On Azure this returns 403.")
        else:
            fail("WRITE succeeded - are you sure this is the read-only key?")
    except exceptions.CosmosHttpResponseError as e:
        ok(f"WRITE blocked: HTTP {e.status_code} (Forbidden). Least privilege works!")


def part3_entra_id():
    step("3) Identity-based access with Microsoft Entra ID (no keys)")
    if not config.flag("USE_ENTRA_ID"):
        warn("USE_ENTRA_ID is false - showing the setup steps only.")
        info("Run these once (Azure CLI) to grant access:")
        for line in RBAC_COMMANDS.strip().splitlines():
            print("      " + line)
        return
    from azure.identity import DefaultAzureCredential
    client = CosmosClient(config.COSMOS_ENDPOINT, credential=DefaultAzureCredential())
    products = client.get_database_client(config.COSMOS_DATABASE).get_container_client("products")
    try:
        n = list(products.query_items("SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True))[0]
        ok(f"Logged in with Entra ID (az login / managed identity). Read {n} products - no key used.")
    except exceptions.CosmosHttpResponseError as e:
        fail(f"HTTP {e.status_code}: your identity has no data-plane role yet. Run the az commands above.")


def part4_checklist():
    step("4) Production security checklist for ShopKart")
    for item in [
        "Keys in Azure Key Vault (or env vars), never in code / Git",
        "Read-only key or Data Reader role for reporting apps",
        "Entra ID + RBAC, then disableLocalAuth=true",
        "Rotate keys: switch app to secondary key -> regenerate primary -> switch back",
        "Networking: Firewall IP rules or Private Endpoint; disable public access in prod",
        "Encryption at rest is ON by default; TLS 1.2+ in transit",
        "Diagnostic logs -> Log Analytics to audit who accessed what",
    ]:
        info(f"[ ] {item}")


def main():
    banner("LAB 4 - Cosmos DB security & access control")
    part1_secrets_hygiene()
    part2_read_only_key()
    part3_entra_id()
    part4_checklist()
    banner("LAB 4 complete")


if __name__ == "__main__":
    main()
