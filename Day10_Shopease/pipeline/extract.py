"""EXTRACT step: read raw orders (CSV) and supplier invoices (PDF)."""
import re
from pathlib import Path

import pandas as pd
import pymupdf

ORDER_COLUMNS = ["order_id", "order_date", "customer_id", "product_id",
                 "category", "quantity", "unit_price", "city", "status"]
INVOICE_COLUMNS = ["invoice_no", "supplier", "invoice_date",
                   "subtotal", "tax", "total", "source_file"]


def extract_orders(raw_dir, file_pattern="orders_*.csv"):
    """Read every orders CSV in raw_dir and combine them into one DataFrame."""
    files = sorted(Path(raw_dir).glob(file_pattern))
    if not files:
        raise FileNotFoundError(f"No files matching {file_pattern} in {raw_dir}")
    frames = []
    for file in files:
        df = pd.read_csv(file, dtype=str)
        missing = set(ORDER_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"{file.name} is missing columns: {sorted(missing)}")
        df["source_file"] = file.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def parse_invoice_text(text):
    """Pull the key fields out of one invoice's text using regular expressions."""
    patterns = {
        "invoice_no": r"Invoice No:\s*(\S+)",
        "supplier": r"Supplier:\s*(.+)",
        "invoice_date": r"Invoice Date:\s*(\d{4}-\d{2}-\d{2})",
        "subtotal": r"Subtotal:\s*INR\s*([\d,]+\.\d{2})",
        "tax": r"GST \(18%\):\s*INR\s*([\d,]+\.\d{2})",
        "total": r"Total Amount:\s*INR\s*([\d,]+\.\d{2})",
    }
    record = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text)
        record[field] = match.group(1).strip() if match else None
    return record


def extract_invoices(invoice_dir):
    """Open each PDF invoice with PyMuPDF, read its text and parse it."""
    records = []
    for pdf_path in sorted(Path(invoice_dir).glob("*.pdf")):
        with pymupdf.open(pdf_path) as doc:
            text = "".join(page.get_text() for page in doc)
        record = parse_invoice_text(text)
        record["source_file"] = pdf_path.name
        records.append(record)
    return pd.DataFrame(records, columns=INVOICE_COLUMNS)
