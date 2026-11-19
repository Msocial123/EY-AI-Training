"""
Module 3.1 - Logging basics: why print() is not enough.

Real life: at 2 AM a customer says "money got deducted but no order".
print() output is gone - nobody was watching the terminal.
Logs are saved WITH time, level and source, so support can find the problem.

Levels (lowest -> highest):
  DEBUG    -> detailed info for developers       ("cart = {...}")
  INFO     -> normal business events             ("order ORD-1 placed")
  WARNING  -> something odd, app still works     ("stock low: 2 left")
  ERROR    -> an operation failed                ("payment failed")
  CRITICAL -> whole app in danger                ("database is down")
"""
import logging

# Configure ONCE, at program start
logging.basicConfig(
    level=logging.INFO,      # show INFO and above (DEBUG is hidden)
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

# One logger per file. __name__ = this module's name -> you know WHERE a log came from
logger = logging.getLogger(__name__)


def add_to_cart(cart, product, qty):
    logger.debug("cart before add: %s", cart)                 # hidden at INFO level
    cart[product["name"]] = cart.get(product["name"], 0) + qty
    logger.info("Added %d x %s to cart", qty, product["name"])

    remaining = product["stock"] - qty
    if remaining <= 2:
        logger.warning("Low stock for %s: only %d left", product["name"], remaining)
    return cart


def charge_customer(amount):
    if amount > 100000:
        logger.error("Payment of Rs.%.2f blocked: above single-transaction limit", amount)
        return False
    logger.info("Payment of Rs.%.2f successful", amount)
    return True


if __name__ == "__main__":
    print("print() just shows text:  Order placed")
    logger.info("Order placed  <- logging adds time, level and source")

    cart = {}
    add_to_cart(cart, {"name": "Wireless Mouse", "stock": 50}, 2)
    add_to_cart(cart, {"name": "Bluetooth Earbuds", "stock": 4}, 2)
    charge_customer(1598.00)
    charge_customer(250000.00)
    logger.critical("Database connection lost - checkout disabled")

    print("\nTip: change level=logging.INFO to logging.DEBUG and run again.")
