"""Creates sample supplier invoice PDFs in data/raw/invoices. Run once before the pipeline."""
from pathlib import Path

import pymupdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INVOICE_DIR = PROJECT_ROOT / "data" / "raw" / "invoices"

SAMPLE_INVOICES = [
    {"invoice_no": "INV-2026-1101", "supplier": "Sunrise Electronics Pvt Ltd",
     "date": "2026-11-17", "subtotal": 125000.00, "tax": 22500.00, "total": 147500.00},
    {"invoice_no": "INV-2026-1102", "supplier": "Kaveri Textiles",
     "date": "2026-11-17", "subtotal": 48000.00, "tax": 8640.00, "total": 56640.00},
    {"invoice_no": "INV-2026-1103", "supplier": "HomeNest Kitchenware",
     "date": "2026-11-18", "subtotal": 30500.00, "tax": 5490.00, "total": 36500.00},
]


def create_invoice_pdf(invoice, output_dir):
    """Write one invoice as a simple one-page PDF and return the file path."""
    lines = [
        "SUPPLIER TAX INVOICE",
        f"Invoice No: {invoice['invoice_no']}",
        f"Supplier: {invoice['supplier']}",
        f"Invoice Date: {invoice['date']}",
        "Bill To: ShopEase Retail Pvt Ltd, Bengaluru",
        f"Subtotal: INR {invoice['subtotal']:,.2f}",
        f"GST (18%): INR {invoice['tax']:,.2f}",
        f"Total Amount: INR {invoice['total']:,.2f}",
    ]
    doc = pymupdf.open()
    page = doc.new_page()
    y_position = 72
    for line in lines:
        page.insert_text((72, y_position), line, fontsize=12)
        y_position += 24
    pdf_path = Path(output_dir) / f"{invoice['invoice_no']}.pdf"
    doc.save(pdf_path)
    doc.close()
    return pdf_path


if __name__ == "__main__":
    INVOICE_DIR.mkdir(parents=True, exist_ok=True)
    for sample in SAMPLE_INVOICES:
        print("Created", create_invoice_pdf(sample, INVOICE_DIR))
