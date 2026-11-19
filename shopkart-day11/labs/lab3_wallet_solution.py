"""
LAB 3 SOLUTION - Logging + custom exceptions

Task: ShopKart Wallet (like Amazon Pay balance)
  - WalletError (base), InsufficientBalanceError, DailyLimitError
  - pay(amount): amount must be > 0, <= balance, and total spent today <= 10,000
  - Log every payment: INFO on success, WARNING on business errors
  - Logs go to console AND to logs/wallet.log
"""
import logging
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("shopkart.wallet")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%H:%M:%S")

console = logging.StreamHandler()
console.setFormatter(formatter)
file_handler = logging.FileHandler(LOG_DIR / "wallet.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(console)
logger.addHandler(file_handler)


class WalletError(Exception):
    pass


class InsufficientBalanceError(WalletError):
    pass


class DailyLimitError(WalletError):
    pass


class Wallet:
    DAILY_LIMIT = 10000

    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance
        self.spent_today = 0

    def pay(self, amount):
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self.balance:
            raise InsufficientBalanceError(f"balance Rs.{self.balance}, needed Rs.{amount}")
        if self.spent_today + amount > self.DAILY_LIMIT:
            raise DailyLimitError(f"daily limit Rs.{self.DAILY_LIMIT} reached")
        self.balance -= amount
        self.spent_today += amount
        logger.info("%s paid Rs.%s, balance now Rs.%s", self.owner, amount, self.balance)


def main():
    wallet = Wallet("priya", balance=12000)
    for amount in [799, 20000, 8500, 1200, -5]:
        try:
            wallet.pay(amount)
        except WalletError as e:
            logger.warning("Payment of Rs.%s refused: %s", amount, e)
        except ValueError as e:
            logger.error("Bad request: %s", e)
    print(f"\nSee {LOG_DIR / 'wallet.log'}")


if __name__ == "__main__":
    main()
