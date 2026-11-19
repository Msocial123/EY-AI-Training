"""
Module 2.3 - Nested models + Serialization (an Order).

Real life: when you tap "Place Order" in a shopping app, the phone sends
ONE JSON with the customer, a LIST of items and an ADDRESS inside it.
  Validation    = JSON / dict  ->  Python object   (checked!)
  Serialization = Python object ->  dict / JSON     (to save or send)
"""
import json
from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field, ValidationError, computed_field


class OrderItem(BaseModel):
    product_id: int
    name: str
    unit_price: float = Field(gt=0)
    quantity: int = Field(ge=1, le=10)          # max 10 units per order

    @computed_field                              # appears in model_dump() too
    @property
    def line_total(self) -> float:
        return round(self.unit_price * self.quantity, 2)


class Address(BaseModel):
    name: str
    line1: str
    city: str
    pincode: str = Field(pattern=r"^[1-9][0-9]{5}$")      # Indian PIN: 6 digits
    phone: str = Field(pattern=r"^[6-9][0-9]{9}$")        # Indian mobile: 10 digits


class Order(BaseModel):
    order_id: str
    customer_email: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$")
    items: List[OrderItem] = Field(min_length=1)          # at least 1 item
    shipping_address: Address                             # nested model
    status: Literal["PLACED", "PAID", "SHIPPED", "DELIVERED", "CANCELLED"] = "PLACED"
    created_at: datetime = Field(default_factory=datetime.now)
    internal_note: str = ""                               # never show to customer

    @computed_field
    @property
    def total(self) -> float:
        return round(sum(item.line_total for item in self.items), 2)


class CourierUpdate(BaseModel):
    """Partner courier API sends camelCase keys. We use snake_case in Python."""
    tracking_id: str = Field(alias="trackingId")
    current_city: str = Field(alias="currentCity")
    expected_delivery: datetime = Field(alias="expectedDelivery")


MOBILE_APP_JSON = """
{
  "order_id": "ORD-2001",
  "customer_email": "priya@example.com",
  "items": [
    {"product_id": 101, "name": "Wireless Mouse", "unit_price": 799, "quantity": 2},
    {"product_id": 102, "name": "Cotton T-Shirt", "unit_price": 499, "quantity": 1}
  ],
  "shipping_address": {
    "name": "Priya Sharma", "line1": "12 MG Road", "city": "Bengaluru",
    "pincode": "560001", "phone": "9876543210"
  },
  "internal_note": "customer called twice about delivery time"
}
"""


def demo_parse_order():
    print("=== 1. JSON from the mobile app -> Order object ===")
    order = Order.model_validate_json(MOBILE_APP_JSON)     # parse + validate in one step
    print("Order       :", order.order_id, "| status:", order.status)
    print("Deliver to  :", order.shipping_address.name, "-", order.shipping_address.city)
    for item in order.items:
        print(f"  {item.quantity} x {item.name:<15} = Rs.{item.line_total}")
    print("Order total : Rs.", order.total)
    return order


def demo_serialization(order):
    print("\n=== 2. Order object -> dict / JSON ===")
    as_dict = order.model_dump()
    print("model_dump() keys:", list(as_dict.keys()))

    # Customer-facing response: hide the internal note
    public_json = order.model_dump_json(indent=2, exclude={"internal_note"})
    print("Customer JSON (internal_note excluded):")
    print(public_json)

    # SMS service only needs a few fields
    sms_payload = order.model_dump(include={"order_id", "total", "status"})
    print("SMS payload:", sms_payload)


def demo_nested_error():
    print("\n=== 3. Errors inside nested data show the exact path ===")
    data = json.loads(MOBILE_APP_JSON)
    data["items"][1]["quantity"] = 25                   # too many units
    data["shipping_address"]["pincode"] = "56001"       # only 5 digits
    try:
        Order.model_validate(data)
    except ValidationError as e:
        for err in e.errors():
            path = " -> ".join(str(x) for x in err["loc"])
            print(f"  {path}: {err['msg']}")


def demo_alias():
    print("\n=== 4. Aliases: camelCase partner API -> snake_case Python ===")
    courier_json = '{"trackingId": "BD123456IN", "currentCity": "Hyderabad", "expectedDelivery": "2026-11-21T18:00:00"}'
    update = CourierUpdate.model_validate_json(courier_json)
    print("tracking_id :", update.tracking_id)
    print("deliver by  :", update.expected_delivery.strftime("%d %b %Y, %I:%M %p"))
    print("Back to partner format:", update.model_dump(by_alias=True, mode="json"))


if __name__ == "__main__":
    order = demo_parse_order()
    demo_serialization(order)
    demo_nested_error()
    demo_alias()
