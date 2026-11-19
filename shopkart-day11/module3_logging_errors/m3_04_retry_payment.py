"""
Module 3.4 - Retry pattern: handling TEMPORARY failures.

Real life: payment gateways (Razorpay, PayU, Stripe) sometimes time out
for a second during big sales. Failing the order immediately loses money.
Companies retry a few times, waiting a little longer each time
("exponential backoff": 0.5s, 1s, 2s ...), and log every attempt.

Rule: retry only TEMPORARY errors (timeout). Never retry "card declined".
"""
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger("shopkart.payments")


class GatewayTimeout(Exception):
    """Temporary - safe to retry."""


class CardDeclined(Exception):
    """Permanent - retrying will not help."""


class FakeGateway:
    """Pretends to be a payment gateway. Fails the first `fail_times` calls."""

    def __init__(self, fail_times, declined=False):
        self.fail_times = fail_times
        self.declined = declined
        self.calls = 0

    def charge(self, amount):
        self.calls += 1
        if self.declined:
            raise CardDeclined("Card declined by bank (insufficient funds)")
        if self.calls <= self.fail_times:
            raise GatewayTimeout(f"timeout on call {self.calls}")
        return f"TXN-{self.calls}-{int(amount)}"


def charge_with_retry(gateway, amount, max_retries=3, base_delay=0.5):
    for attempt in range(1, max_retries + 1):
        try:
            txn = gateway.charge(amount)
            logger.info("Attempt %d: SUCCESS %s", attempt, txn)
            return txn
        except GatewayTimeout as e:
            if attempt == max_retries:
                logger.error("Attempt %d: %s - giving up", attempt, e)
                raise
            wait = base_delay * (2 ** (attempt - 1))       # 0.5, 1.0, 2.0 ...
            logger.warning("Attempt %d: %s - retrying in %.1fs", attempt, e, wait)
            time.sleep(wait)
        except CardDeclined as e:
            logger.error("Attempt %d: %s - NOT retrying", attempt, e)
            raise


if __name__ == "__main__":
    print("\n--- Case 1: gateway slow twice, then works ---")
    charge_with_retry(FakeGateway(fail_times=2), 1598)

    print("\n--- Case 2: gateway down for long ---")
    try:
        charge_with_retry(FakeGateway(fail_times=10), 1598)
    except GatewayTimeout:
        print("Show customer: 'Payment pending. We will update you in 30 minutes.'")

    print("\n--- Case 3: card declined (permanent) ---")
    try:
        charge_with_retry(FakeGateway(fail_times=0, declined=True), 1598)
    except CardDeclined:
        print("Show customer: 'Card declined. Please use another card or UPI.'")
