"""Run this FIRST:  python check_setup.py
Checks Python, packages, your .env file and the connection to Cosmos DB."""
import sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ok = True


def report(passed, label, hint=""):
    global ok
    ok &= passed
    print(("  [OK]   " if passed else "  [FAIL] ") + label + ("" if passed or not hint else f"\n         -> {hint}"))


print("\nQuickBite setup check\n" + "-" * 50)
report(sys.version_info >= (3, 9), f"Python {sys.version.split()[0]}", "Install Python 3.10 or newer from python.org")
if sys.prefix != sys.base_prefix:
    report(True, "Virtual environment active")
else:
    print("  [TIP]  No virtual environment active - fine, but .venv is recommended (Setup Guide step 5)")

missing = []
for mod in ("azure.cosmos", "azure.identity", "dotenv"):
    try:
        __import__(mod)
    except ImportError:
        missing.append(mod)
report(not missing, "Packages installed" + (f" (missing: {', '.join(missing)})" if missing else ""),
       "Run:  pip install -r requirements.txt")
if missing:
    sys.exit("\nFix the items above, then run again.\n")

report((ROOT / ".env").exists(), ".env file exists", "Copy .env.example to .env and fill in endpoint + key")
if not (ROOT / ".env").exists():
    sys.exit("\nFix the items above, then run again.\n")

sys.path.insert(0, str(ROOT))
from qb import config  # noqa: E402  (loads .env)

emu = config._flag("COSMOS_EMULATOR")
if emu:
    print(f"  [INFO] Using LOCAL EMULATOR at {config._EMULATOR_URL}")
else:
    ep = os.getenv("COSMOS_ENDPOINT", "")
    report(ep.startswith("https://") and "<" not in ep and ".documents.azure.com" in ep,
           f"COSMOS_ENDPOINT looks valid ({ep[:60]})", "Copy the URI from Portal -> Keys")
    key = os.getenv("COSMOS_KEY", "")
    report(len(key) > 40 and "<" not in key and " " not in key, "COSMOS_KEY looks valid",
           "Copy PRIMARY KEY from Portal -> Keys (no spaces, no quotes)")

try:
    client = config.get_client()
    acct = client.get_database_account()
    regions = [l["name"] for l in acct.ReadableLocations] or ["local"]
    report(True, f"Connected to Cosmos DB  (regions: {', '.join(regions)})")
    c = config.get_container("SetupCheck", "/pk", client=client)
    c.upsert_item({"id": "ping", "pk": "ping", "msg": "hello"})
    c.read_item("ping", partition_key="ping")
    report(True, f"Write + read test passed  (database: {config.DB_NAME})")
    client.get_database_client(config.DB_NAME).delete_container("SetupCheck")
except SystemExit as e:
    report(False, "Connection", str(e))
except Exception as e:
    msg = str(e).splitlines()[0][:160]
    hint = "Check endpoint/key, internet/proxy, Portal -> Networking (allow your IP)"
    if "offer" in msg.lower() or "serverless" in msg.lower():
        hint = "Your account is Serverless: set COSMOS_SERVERLESS=true in .env"
    elif "localhost" in msg.lower() or "refused" in msg.lower() or "connect" in msg.lower() and config._flag("COSMOS_EMULATOR"):
        hint = ("Is the emulator running? Open Docker Desktop, then run:  docker ps   "
                "(Mac/Docker uses http://localhost:8081/ in COSMOS_EMULATOR_URL)")
    report(False, f"Connection: {type(e).__name__}: {msg}", hint)

print("-" * 50)
print("All good! Next:  python live/01_connect.py\n" if ok else "Fix the [FAIL] items above, then run again.\n")
