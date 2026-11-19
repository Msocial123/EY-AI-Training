"""
Module 3.3 - Error handling with CUSTOM exceptions.

Real life: checkout can fail for many reasons - out of stock, bad coupon,
payment declined. Each needs a DIFFERENT reaction:
  OutOfStockError    -> show "Notify me when available"
  InvalidCouponError -> show "Coupon expired", keep the order going
  PaymentFailedError -> show "Try another card", log it for finance team
A custom exception hierarchy makes this clean.

    ShopKartError                 (base - catch ALL our business errors)
     |-- OutOfStockError
     |-- InvalidCouponError
     |-- PaymentFailedError
"""
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s | %(message)s")
logger = logging.getLogger("shopkart.checkout")


# ---------- 1. Our own exception classes ----------
class ShopKartError(Exception):
    """Base class for all ShopKart business errors."""


class OutOfStockError(ShopKartError):
    def __init__(self, product_name, requested, available):
        self.product_name = product_name
        self.requested = requested
        self.available = available
        super().__init__(f"{product_name}: requested {requested}, only {available} left")


class InvalidCouponError(ShopKartError):
    pass


class PaymentFailedError(ShopKartError):
    pass


# ---------- 2. Business functions that RAISE errors ----------
INVENTORY = {"Wireless Mouse": 50, "Bluetooth Earbuds": 4, "Gaming Laptop": 5}
COUPONS = {"WELCOME10": 10, "FEST20": 20}


def reserve_stock(product_name, qty):
    available = INVENTORY.get(product_name, 0)
    if qty > available:
        raise OutOfStockError(product_name, qty, available)
    INVENTORY[product_name] = available - qty


def apply_coupon(amount, code):
    if code is None:
        return amount
    if code not in COUPONS:
        raise InvalidCouponError(f"Coupon '{code}' is invalid or expired")
    return amount * (100 - COUPONS[code]) / 100


def call_bank(amount):
    if amount > 50000:
        # A low-level error from the bank's library
        raise ConnectionError("Bank gateway timeout after 5s")
    return "TXN-" + str(int(amount * 100))


def pay(amount):
    try:
        return call_bank(amount)
    except ConnectionError as e:
        # Convert a technical error into a business error.
        # "from e" keeps the original error for debugging (exception chaining).
        raise PaymentFailedError(f"Could not charge Rs.{amount:.2f}") from e


# ---------- 3. Checkout: try / except / else / finally ----------
def checkout(product_name, qty, unit_price, coupon=None):
    print(f"\n>>> Checkout: {qty} x {product_name}, coupon={coupon}")
    try:
        reserve_stock(product_name, qty)
        amount = unit_price * qty
        try:
            amount = apply_coupon(amount, coupon)
        except InvalidCouponError as e:
            logger.warning("%s - continuing without coupon", e)   # soft failure
        txn_id = pay(amount)
    except OutOfStockError as e:
        logger.warning("Out of stock -> %s", e)
        return {"ok": False, "message": f"Only {e.available} left. Notify me?"}
    except PaymentFailedError:
        logger.exception("Payment failed")            # logs the full traceback too
        return {"ok": False, "message": "Payment failed. Try another method."}
    else:
        logger.info("Order confirmed, txn=%s, paid Rs.%.2f", txn_id, amount)
        return {"ok": True, "txn": txn_id}
    finally:
        logger.info("Checkout attempt finished for %s", product_name)   # ALWAYS runs


if __name__ == "__main__":
    print(checkout("Wireless Mouse", 2, 799, coupon="FEST20"))     # success
    print(checkout("Bluetooth Earbuds", 10, 1999))                 # out of stock
    print(checkout("Wireless Mouse", 1, 799, coupon="DIWALI99"))   # bad coupon, still OK
    print(checkout("Gaming Laptop", 1, 74999))                     # payment fails
