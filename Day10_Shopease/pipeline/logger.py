"""Creates a logger that writes to the console and to a daily log file."""
import logging
from datetime import date
from pathlib import Path


def get_logger(log_dir, name="shopease_pipeline"):
    """Return a configured logger. Calling it again returns the same logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"pipeline_{date.today():%Y-%m-%d}.log"
    formatter = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
