"""
Module 1.3 - INI files and .env secrets.

Real life rule: settings (host, port) can live in files in Git,
but SECRETS (passwords, API keys) must NEVER be pushed to Git.
They go in environment variables / a .env file that is in .gitignore.
"""
import configparser
import os
from pathlib import Path

from dotenv import load_dotenv   # pip install python-dotenv

BASE_DIR = Path(__file__).parent
REPO_ROOT = BASE_DIR.parent


def read_ini():
    print("=== 1. Reading app.ini ===")
    config = configparser.ConfigParser()
    config.read(BASE_DIR / "config" / "app.ini")

    db_host = config["database"]["host"]
    db_port = config.getint("database", "port")      # converts to int
    print(f"Database -> {db_host}:{db_port} / {config['database']['name']}")
    print(f"Email    -> {config['email']['sender']} via {config['email']['smtp_server']}")
    print("Sections :", config.sections())
    return config


def mask(secret):
    """Show only last 4 chars - never print full secrets in logs!"""
    if not secret:
        return "<not set>"
    return "*" * (len(secret) - 4) + secret[-4:]


def read_secrets():
    print("\n=== 2. Reading secrets from .env ===")
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(".env file found and loaded")
    else:
        print("WARNING: .env not found. Copy .env.example to .env (see commands sheet)")

    db_password = os.getenv("DB_PASSWORD")
    payment_key = os.getenv("PAYMENT_API_KEY")
    environment = os.getenv("SHOPKART_ENV", "development")   # default value

    print("DB_PASSWORD     :", mask(db_password))
    print("PAYMENT_API_KEY :", mask(payment_key))
    print("SHOPKART_ENV    :", environment)


if __name__ == "__main__":
    read_ini()
    read_secrets()
