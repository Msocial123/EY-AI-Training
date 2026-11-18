"""Loads pipeline settings from config/settings.json."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = PROJECT_ROOT / "config" / "settings.json"
REQUIRED_KEYS = ["raw_dir", "staging_dir", "processed_dir", "database_path", "log_dir", "gst_rate"]


def load_settings(settings_file=SETTINGS_FILE):
    """Read the JSON settings file and return it as a dictionary."""
    settings_file = Path(settings_file)
    if not settings_file.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_file}")
    with open(settings_file, "r", encoding="utf-8") as file:
        settings = json.load(file)
    missing = [key for key in REQUIRED_KEYS if key not in settings]
    if missing:
        raise KeyError(f"Missing settings: {missing}")
    return settings


def resolve_path(relative_path):
    """Turn a path from settings.json into an absolute path inside the project."""
    return PROJECT_ROOT / relative_path
