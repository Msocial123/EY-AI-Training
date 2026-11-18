"""Unit tests for the pipeline logic. Run from the project folder: python -m pytest -v"""
import pandas as pd

from pipeline.extract import parse_invoice_text
from pipeline.transform import add_order_totals, clean_orders, validate_invoices

VALID_STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED"]


def make_order(**changes):
    """Build one valid raw order row; pass keyword arguments to break it on purpose."""
    order = {"order_id": "ORD-1", "order_date": "2026-11-18", "customer_id": "C-1",
             "product_id": "P-1", "category": "fashion", "quantity": "2",
             "unit_price": "500.00", "city": " pune ", "status": "placed"}
    order.update(changes)
    return order


def test_clean_orders_rejects_bad_rows():
    raw = pd.DataFrame([make_order(),
                        make_order(order_id="ORD-2", customer_id=""),
                        make_order(order_id="ORD-3", quantity="-1")])
    clean, rejected = clean_orders(raw, VALID_STATUSES)
    assert list(clean["order_id"]) == ["ORD-1"]
    assert "missing customer_id" in rejected.loc[0, "reject_reason"]
    assert "invalid quantity" in rejected.loc[1, "reject_reason"]


def test_clean_orders_standardises_text_and_removes_duplicates():
    raw = pd.DataFrame([make_order(), make_order()])
    clean, rejected = clean_orders(raw, VALID_STATUSES)
    assert len(clean) == 1 and len(rejected) == 0
    assert clean.loc[0, "city"] == "Pune"
    assert clean.loc[0, "status"] == "PLACED"


def test_add_order_totals_applies_gst_and_revenue_flag():
    raw = pd.DataFrame([make_order(), make_order(order_id="ORD-2", status="cancelled")])
    clean, _ = clean_orders(raw, VALID_STATUSES)
    orders = add_order_totals(clean, 0.18)
    assert orders.loc[0, "line_amount"] == 1000.00
    assert orders.loc[0, "gst_amount"] == 180.00
    assert orders.loc[0, "order_total"] == 1180.00
    assert list(orders["counts_as_revenue"]) == [True, False]


def test_parse_and_validate_invoice():
    text = ("Invoice No: INV-9\nSupplier: Demo Traders\nInvoice Date: 2026-11-18\n"
            "Subtotal: INR 1,000.00\nGST (18%): INR 180.00\nTotal Amount: INR 1,200.00\n")
    record = parse_invoice_text(text)
    assert record["invoice_no"] == "INV-9"
    assert record["subtotal"] == "1,000.00"
    checked = validate_invoices(pd.DataFrame([record]))
    assert bool(checked.loc[0, "is_valid"]) is False
