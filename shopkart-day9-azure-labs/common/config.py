"""
Central place that reads settings from the .env file.

RULE #1 of cloud security: secrets (keys, connection strings) NEVER go in code.
They live in a .env file (which is in .gitignore) or in environment variables.
"""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # python-dotenv not installed -> plain environment variables still work
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets"
SAMPLE_OUTPUTS_DIR = ROOT / "sample_outputs"


def get(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is not None:
        value = value.strip()
    return value or default


def require(name: str) -> str:
    """Read a setting that MUST exist. Gives a friendly error instead of a crash."""
    value = get(name)
    if not value:
        print(f"\n[CONFIG ERROR] '{name}' is not set.")
        print("  1. Copy .env.example to .env")
        print(f"  2. Fill in {name}")
        print("  3. Run the script again\n")
        sys.exit(1)
    return value


def flag(name: str) -> bool:
    return (get(name, "false") or "false").lower() in ("1", "true", "yes", "y")


# ---- Cosmos DB --------------------------------------------------------------
COSMOS_ENDPOINT = get("COSMOS_ENDPOINT", "http://localhost:8081")
COSMOS_DATABASE = get("COSMOS_DATABASE", "shopkart")
IS_COSMOS_EMULATOR = "localhost" in (COSMOS_ENDPOINT or "") or "127.0.0.1" in (COSMOS_ENDPOINT or "")

# ---- Blob Storage -----------------------------------------------------------
STORAGE_CONNECTION_STRING = get("STORAGE_CONNECTION_STRING", "UseDevelopmentStorage=true")
IS_AZURITE = "UseDevelopmentStorage=true" in (STORAGE_CONNECTION_STRING or "") or "127.0.0.1:10000" in (STORAGE_CONNECTION_STRING or "")

# ---- AI services ------------------------------------------------------------
VISION_ENDPOINT = get("VISION_ENDPOINT")
VISION_KEY = get("VISION_KEY")
DOCINTEL_ENDPOINT = get("DOCINTEL_ENDPOINT")
DOCINTEL_KEY = get("DOCINTEL_KEY")
