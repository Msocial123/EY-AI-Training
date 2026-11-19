"""
Module 3.2 - Production logging: console + rotating file, configured from YAML.

Real life setup used in companies:
  - Console shows INFO and above (for the developer watching)
  - File keeps DEBUG and above (for investigating problems later)
  - File "rotates": when it reaches 1 MB a new file starts, old ones are kept
    (shopkart.log, shopkart.log.1, shopkart.log.2 ...) so the disk never fills up
  - Config lives in logging.yaml, so ops team can change levels without code changes
"""
import logging
import logging.config
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)                       # handler needs the folder to exist
    with open(BASE_DIR / "logging.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["handlers"]["file"]["filename"] = str(LOG_DIR / "shopkart.log")
    logging.config.dictConfig(config)


setup_logging()
logger = logging.getLogger("shopkart.orders")         # named logger


def place_order(order_id, customer, amount):
    logger.debug("Validating order %s for %s", order_id, customer)    # file only
    logger.info("Order %s placed by %s, amount Rs.%.2f", order_id, customer, amount)
    if amount > 50000:
        logger.warning("High value order %s - send for fraud check", order_id)


if __name__ == "__main__":
    place_order("ORD-3001", "priya@example.com", 2097.00)
    place_order("ORD-3002", "rahul@example.com", 74999.00)

    logging.getLogger("shopkart.payments").info("Refund started for ORD-2990")

    print(f"\nNow open {LOG_DIR / 'shopkart.log'} - it also has the DEBUG lines.")
