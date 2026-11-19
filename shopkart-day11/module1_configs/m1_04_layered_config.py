"""
Module 1.4 - Layered configuration (how real companies do it).

Priority (lowest -> highest):
   1. settings.yaml            -> defaults for everyone
   2. settings.<env>.yaml      -> overrides for that environment (prod)
   3. Environment variables    -> overrides at run time (Docker / Azure)

Same code runs on a laptop, in testing and in production.
"""
import copy
import os
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent / "config"


def deep_merge(base, override):
    """Merge override dict INTO base dict, going inside nested dicts."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(env=None):
    env = env or os.getenv("SHOPKART_ENV", "development")

    # Layer 1: base file
    with open(CONFIG_DIR / "settings.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Layer 2: environment file (only if it exists)
    env_file = CONFIG_DIR / f"settings.{env}.yaml"
    if env_file.exists():
        with open(env_file, encoding="utf-8") as f:
            config = deep_merge(config, yaml.safe_load(f))

    # Layer 3: environment variables win over everything
    if os.getenv("SHOPKART_GST_PERCENT"):
        config["store"]["gst_percent"] = float(os.getenv("SHOPKART_GST_PERCENT"))
    if os.getenv("SHOPKART_PAYMENT_TIMEOUT"):
        config["payment"]["timeout_seconds"] = int(os.getenv("SHOPKART_PAYMENT_TIMEOUT"))

    return config


def show(config, title):
    print(f"=== {title} ===")
    print("  environment :", config["app"]["environment"])
    print("  debug       :", config["app"]["debug"])
    print("  payment     :", config["payment"]["provider"],
          f"(timeout {config['payment']['timeout_seconds']}s)")
    print("  gst_percent :", config["store"]["gst_percent"])


if __name__ == "__main__":
    show(load_config("development"), "DEVELOPMENT")
    show(load_config("prod"), "PRODUCTION")
    show(load_config(), "FROM SHOPKART_ENV variable (current shell)")
