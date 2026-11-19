"""
Module 2.4 - Validate your CONFIG with Pydantic (Module 1 + Module 2 together).

Real life incident: someone typed  gst_percent: "eighteen"  in a YAML file.
Without validation the app starts fine... and crashes at 9 PM during a sale
when the first customer checks out.
With Pydantic the app refuses to START with a bad config. This is "fail fast".
"""
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field, ValidationError

CONFIG_FILE = Path(__file__).parent.parent / "module1_configs" / "config" / "settings.yaml"


class AppSection(BaseModel):
    name: str
    environment: str
    debug: bool


class StoreSection(BaseModel):
    currency: str = Field(min_length=3, max_length=3)
    gst_percent: float = Field(ge=0, le=28)
    free_shipping_above: float = Field(ge=0)
    shipping_fee: float = Field(ge=0)
    low_stock_threshold: int = Field(ge=0)


class PaymentSection(BaseModel):
    provider: str
    timeout_seconds: int = Field(gt=0, le=60)
    max_retries: int = Field(ge=0, le=5)


class FeaturesSection(BaseModel):
    cash_on_delivery: bool
    coupons_enabled: bool


class Coupon(BaseModel):
    code: str
    discount_percent: float = Field(gt=0, le=90)


class ShopKartConfig(BaseModel):
    app: AppSection
    store: StoreSection
    payment: PaymentSection
    features: FeaturesSection
    coupons: List[Coupon] = []


def load_config(raw: dict) -> ShopKartConfig:
    return ShopKartConfig.model_validate(raw)


if __name__ == "__main__":
    with open(CONFIG_FILE, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    print("=== 1. Good config ===")
    config = load_config(raw)
    # Now we use DOTS instead of ["keys"] - editor autocomplete works!
    print("App      :", config.app.name, "/", config.app.environment)
    print("GST      :", config.store.gst_percent, "%")
    print("Payment  :", config.payment.provider, f"timeout={config.payment.timeout_seconds}s")
    print("Coupons  :", [c.code for c in config.coupons])

    print("\n=== 2. Someone made typos in the config ===")
    raw["store"]["gst_percent"] = "eighteen"
    raw["payment"]["timeout_seconds"] = 0
    raw["coupons"].append({"code": "MEGA100", "discount_percent": 100})
    try:
        load_config(raw)
        print("App started (this should NOT happen)")
    except ValidationError as e:
        print("App will NOT start. Fix settings.yaml:")
        for err in e.errors():
            path = ".".join(str(x) for x in err["loc"])
            print(f"  {path}: {err['msg']}")
