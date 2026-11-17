"""
LAB 6 - Azure AI Document Intelligence (prebuilt invoice + receipt models)
=========================================================================
Curriculum topic : "Azure Doc Intelligence"

OCR (lab 5) gives you LINES OF TEXT.
Document Intelligence gives you NAMED FIELDS: InvoiceId, VendorName, Items[], Total...
It already "knows" what an invoice or a receipt looks like (prebuilt models).

ShopKart use cases
  A) Accounts Payable: suppliers email ~500 PDF invoices a day. A human typing them
     into the ERP takes 4-5 minutes each. We extract fields automatically and run a
     "PO match": does the invoice agree with what we ordered (Purchase Order)?
  B) Employee expenses: staff upload store receipts; we read merchant, date, total.

Models used
  prebuilt-invoice  -> invoices          prebuilt-receipt -> receipts
  prebuilt-read     -> just OCR text     prebuilt-layout  -> text + tables + structure
  prebuilt-idDocument, prebuilt-tax.us..., or YOUR OWN custom model (train on 5+ samples)

Modes: ONLINE (DOCINTEL_ENDPOINT + DOCINTEL_KEY set) or OFFLINE (sample_outputs/*.json)

Run:  python labs/lab06_document_intelligence.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import config  # noqa: E402
from common.clients import docintel_client  # noqa: E402
from common.pretty import banner, step, info, ok, warn, fail, table  # noqa: E402

REVIEW_THRESHOLD = 0.80

# What ShopKart's purchase team actually ORDERED (normally read from the ERP / Cosmos DB)
PURCHASE_ORDER = {
    "poNumber": "SK-PO-7781",
    "vendor": "TechNova Supplies Pvt. Ltd.",
    "lines": {
        "boAt Rockerz 450 Bluetooth Headphones": {"qty": 50, "unitPrice": 1000.00},   # agreed price 1000!
        "Samsung Galaxy M35 5G (8GB/128GB)": {"qty": 20, "unitPrice": 14200.00},
        "USB-C Fast Charger 25W": {"qty": 100, "unitPrice": 450.00},
    },
}


# ----------------------------------------------------------------- analyse --
def analyze(model_id: str, file_path: Path, sample_name: str) -> dict:
    client = docintel_client()
    if client is None:
        warn(f"OFFLINE mode: loading sample_outputs/{sample_name}.json")
        return json.loads((config.SAMPLE_OUTPUTS_DIR / f"{sample_name}.json").read_text())

    info(f"ONLINE mode: sending {file_path.name} to model '{model_id}' ...")
    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document(model_id, body=f)   # long-running operation
    result = poller.result()                                      # waits until Azure finishes
    data = result.as_dict()
    out = config.SAMPLE_OUTPUTS_DIR / f"{sample_name}.live.json"
    out.write_text(json.dumps(data, indent=1, default=str))
    ok(f"saved raw response to {out.relative_to(config.ROOT)}")
    return data


def value_of(field: dict | None):
    """Turn one Document Intelligence field (dict form) into a plain Python value."""
    if not field:
        return None
    t = field.get("type")
    if t == "currency":
        return (field.get("valueCurrency") or {}).get("amount")
    if t == "array":
        return [value_of(x) for x in field.get("valueArray", [])]
    if t == "object":
        return {k: value_of(v) for k, v in (field.get("valueObject") or {}).items()}
    key = {
        "string": "valueString", "date": "valueDate", "number": "valueNumber",
        "integer": "valueInteger", "time": "valueTime", "phoneNumber": "valuePhoneNumber",
    }.get(t)
    return field.get(key) if key and field.get(key) is not None else field.get("content")


def low_confidence_fields(fields: dict, prefix="") -> list[tuple[str, float]]:
    found = []
    for name, f in fields.items():
        if f.get("confidence") is not None and f["confidence"] < REVIEW_THRESHOLD:
            found.append((prefix + name, f["confidence"]))
        if f.get("type") == "array":
            for i, item in enumerate(f.get("valueArray", [])):
                found += low_confidence_fields(item.get("valueObject") or {}, f"{prefix}{name}[{i}].")
    return found


# -------------------------------------------------------- A) invoice + PO match --
def invoice_demo(pdf_path: Path | None = None) -> dict:
    pdf_path = pdf_path or config.ASSETS_DIR / "invoice_technova.pdf"
    step(f"A) Supplier invoice PDF -> structured data ({pdf_path.name})")
    result = analyze("prebuilt-invoice", pdf_path, "docint_invoice")
    doc = result["documents"][0]
    fields = doc["fields"]

    header = [{"field": k, "value": value_of(fields.get(k)), "confidence": fields.get(k, {}).get("confidence")}
              for k in ("VendorName", "InvoiceId", "PurchaseOrder", "InvoiceDate", "DueDate",
                        "SubTotal", "TotalTax", "InvoiceTotal")]
    table(header)

    items = value_of(fields.get("Items")) or []
    step("Line items:")
    table(items, ["Description", "Quantity", "UnitPrice", "Amount"], max_width=40)

    step("3-way PO match: does the invoice agree with what we ordered?")
    problems = []
    if value_of(fields.get("PurchaseOrder")) != PURCHASE_ORDER["poNumber"]:
        problems.append("PO number mismatch")
    po_lines = {name.lower().strip(): line for name, line in PURCHASE_ORDER["lines"].items()}
    for it in items:
        # normalise text: real OCR output may differ in case / extra spaces
        po_line = po_lines.get((it["Description"] or "").lower().strip())
        if not po_line:
            problems.append(f"'{it['Description']}' was never ordered")
            continue
        if it["Quantity"] != po_line["qty"]:
            problems.append(f"{it['Description']}: qty {it['Quantity']} vs PO {po_line['qty']}")
        if abs((it["UnitPrice"] or 0) - po_line["unitPrice"]) > 0.01:
            diff = (it["UnitPrice"] - po_line["unitPrice"]) * it["Quantity"]
            problems.append(f"{it['Description']}: unit price {it['UnitPrice']} vs PO {po_line['unitPrice']} "
                            f"(overcharge Rs.{diff:,.0f})")
    total_items = sum(i["Amount"] for i in items)
    if abs(total_items - value_of(fields["SubTotal"])) > 1:
        problems.append("Line items do not add up to SubTotal")

    for p in problems:
        fail(p)
    if not problems:
        ok("Invoice matches PO -> auto-approve for payment")

    shaky = low_confidence_fields(fields)
    for name, conf in shaky:
        warn(f"Low confidence ({conf}) on {name} -> highlight for the AP clerk")

    status = "ON_HOLD" if problems else ("NEEDS_REVIEW" if shaky else "APPROVED")
    record = {
        "id": value_of(fields["InvoiceId"]),
        "vendorName": value_of(fields["VendorName"]),          # partition key in Cosmos 'invoices'
        "poNumber": value_of(fields.get("PurchaseOrder")),
        "invoiceDate": str(value_of(fields["InvoiceDate"])),
        "dueDate": str(value_of(fields.get("DueDate"))),
        "total": value_of(fields["InvoiceTotal"]),
        "items": items,
        "status": status,
        "issues": problems,
        "lowConfidenceFields": [n for n, _ in shaky],
        "sourceFile": pdf_path.name,
    }
    step(f"Final decision: {status}. This JSON is what we store in Cosmos DB (lab 9):")
    info(json.dumps({k: record[k] for k in ("id", "vendorName", "total", "status")}, ensure_ascii=False))
    return record


# --------------------------------------------------------------- B) receipt --
def receipt_demo():
    step("B) Employee expense claim: store receipt photo (assets/receipt_store.png)")
    result = analyze("prebuilt-receipt", config.ASSETS_DIR / "receipt_store.png", "docint_receipt")
    fields = result["documents"][0]["fields"]
    claim = {
        "merchant": value_of(fields.get("MerchantName")),
        "date": str(value_of(fields.get("TransactionDate"))),
        "total": value_of(fields.get("Total")),
        "items": len(value_of(fields.get("Items")) or []),
    }
    table([claim])
    limit = 2000
    if claim["total"] and claim["total"] > limit:
        warn(f"Total Rs.{claim['total']} exceeds auto-approval limit Rs.{limit} -> manager approval")
    else:
        ok("Within limit -> auto-reimburse")


def main():
    banner("LAB 6 - Azure AI Document Intelligence")
    record = invoice_demo()
    receipt_demo()
    (config.SAMPLE_OUTPUTS_DIR / "invoice_record.json").write_text(json.dumps(record, indent=2, default=str))
    banner("LAB 6 complete - record saved to sample_outputs/invoice_record.json")


if __name__ == "__main__":
    main()
