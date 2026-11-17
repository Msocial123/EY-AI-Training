"""
Generates every sample file used in the Day 9 labs.

    python tools/make_sample_assets.py

Creates:
  data/products.json        -> ShopKart product catalogue (goes into Cosmos DB)
  data/orders.json          -> ShopKart customer orders (goes into Cosmos DB)
  assets/product_label.png  -> photo-style product label (OCR lab)
  assets/return_note.png    -> customer's handwritten-style return note (OCR lab)
  assets/invoice_technova.pdf -> supplier invoice (Document Intelligence lab)
  assets/receipt_store.png  -> store receipt (Document Intelligence lab)
  assets/product_images/*.png -> product photos (Blob Storage lab)

You do NOT need to run this - the files are already in the repo.
It is here so you can see how the data was made and create more.
"""
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
random.seed(9)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_HAND = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:  # running on a machine without DejaVu fonts
        return ImageFont.load_default()


# --------------------------------------------------------------------------
# 1. Product catalogue
# --------------------------------------------------------------------------
PRODUCTS = [
    # sku, name, category, brand, price, stock, rating, tags, seller city
    ("ELEC-1001", "Samsung Galaxy M35 5G (8GB/128GB)", "Electronics", "Samsung", 16999, 42, 4.3, ["bestseller", "5g", "mobile"], "Hyderabad"),
    ("ELEC-1002", "Apple iPhone 15 (128GB)", "Electronics", "Apple", 69900, 8, 4.6, ["premium", "mobile"], "Bengaluru"),
    ("ELEC-1003", "boAt Rockerz 450 Bluetooth Headphones", "Electronics", "boAt", 1499, 230, 4.1, ["bestseller", "audio"], "Delhi"),
    ("ELEC-1004", "Lenovo IdeaPad Slim 5 Laptop", "Electronics", "Lenovo", 58990, 3, 4.4, ["laptop", "student"], "Bengaluru"),
    ("ELEC-1005", "Mi 43-inch 4K Smart TV", "Electronics", "Xiaomi", 26999, 15, 4.2, ["tv", "festive-deal"], "Chennai"),
    ("FASH-2001", "Men's Cotton Slim Fit Shirt", "Fashion", "Peter England", 1299, 120, 4.0, ["men", "office-wear"], "Tiruppur"),
    ("FASH-2002", "Women's Banarasi Silk Saree", "Fashion", "Kanchi Weaves", 4599, 25, 4.7, ["women", "festive-deal", "bestseller"], "Varanasi"),
    ("FASH-2003", "Running Shoes Ultraboost", "Fashion", "Adidas", 7999, 4, 4.5, ["sports", "footwear"], "Mumbai"),
    ("FASH-2004", "Kids Denim Jacket", "Fashion", "Max", 999, 60, 3.9, ["kids"], "Hyderabad"),
    ("HOME-3001", "Prestige Induction Cooktop 2000W", "Home & Kitchen", "Prestige", 2799, 75, 4.2, ["kitchen", "bestseller"], "Bengaluru"),
    ("HOME-3002", "Milton Steel Water Bottle 1L", "Home & Kitchen", "Milton", 549, 400, 4.4, ["kitchen", "eco"], "Mumbai"),
    ("HOME-3003", "Wakefit Orthopaedic Mattress (Queen)", "Home & Kitchen", "Wakefit", 12499, 2, 4.3, ["bedroom", "festive-deal"], "Bengaluru"),
    ("HOME-3004", "Philips Air Fryer HD9252", "Home & Kitchen", "Philips", 7499, 18, 4.5, ["kitchen", "premium"], "Pune"),
    ("BOOK-4001", "Atomic Habits", "Books", "Penguin", 499, 300, 4.8, ["self-help", "bestseller"], "Delhi"),
    ("BOOK-4002", "Wings of Fire - A. P. J. Abdul Kalam", "Books", "Universities Press", 299, 150, 4.9, ["biography", "student"], "Hyderabad"),
    ("BOOK-4003", "Cracking the Coding Interview", "Books", "CareerCup", 699, 45, 4.6, ["programming", "student"], "Bengaluru"),
    ("GROC-5001", "Tata Tea Gold 1kg", "Grocery", "Tata", 560, 500, 4.4, ["daily-needs", "bestseller"], "Kolkata"),
    ("GROC-5002", "Aashirvaad Atta 10kg", "Grocery", "ITC", 465, 350, 4.5, ["daily-needs"], "Hyderabad"),
    ("GROC-5003", "Organic Cold-Pressed Groundnut Oil 1L", "Grocery", "Two Brothers", 399, 0, 4.2, ["organic", "eco"], "Pune"),
    ("GROC-5004", "Haldiram's Bhujia 1kg", "Grocery", "Haldiram's", 240, 90, 4.3, ["snacks"], "Nagpur"),
]

VARIANT_COLORS = {
    "Electronics": ["Black", "Blue", "Silver"],
    "Fashion": ["Red", "Navy", "White"],
    "Home & Kitchen": ["Steel", "Black"],
}


def build_products():
    items = []
    for sku, name, cat, brand, price, stock, rating, tags, city in PRODUCTS:
        doc = {
            "id": sku,                      # Cosmos DB needs an 'id' (string)
            "sku": sku,
            "name": name,
            "category": cat,                # <- partition key of 'products'
            "brand": brand,
            "price": price,
            "currency": "INR",
            "stock": stock,
            "rating": rating,
            "tags": tags,
            "seller": {"name": f"{brand} Authorised Seller", "city": city},
        }
        # Semi-structured on purpose: only some products have variants/discounts/specs
        if cat in VARIANT_COLORS:
            doc["variants"] = [
                {"color": c, "stock": max(0, stock // len(VARIANT_COLORS[cat]) - i * 3)}
                for i, c in enumerate(VARIANT_COLORS[cat])
            ]
        if "festive-deal" in tags:
            doc["discount"] = {"percent": 20, "validTill": "2026-11-30"}
        if cat == "Electronics":
            doc["specs"] = {"warrantyMonths": 12, "returnableDays": 7}
        if cat == "Books":
            doc["specs"] = {"format": "Paperback", "language": "English"}
        items.append(doc)
    return items


CUSTOMERS = [
    ("CUST-001", "Ananya Rao", "Hyderabad"),
    ("CUST-002", "Rahul Verma", "Delhi"),
    ("CUST-003", "Priya Nair", "Kochi"),
    ("CUST-004", "Arjun Reddy", "Hyderabad"),
    ("CUST-005", "Sneha Patil", "Pune"),
    ("CUST-006", "Mohammed Irfan", "Bengaluru"),
]
STATUSES = ["Placed", "Packed", "Shipped", "Delivered", "Delivered", "Delivered", "Cancelled", "Returned"]
PAYMENTS = ["UPI", "UPI", "Card", "COD", "NetBanking"]


def build_orders(products):
    orders = []
    n = 1
    for cust_id, cust_name, city in CUSTOMERS:
        for _ in range(random.randint(2, 4)):
            picks = random.sample(products, random.randint(1, 3))
            lines = [
                {"sku": p["sku"], "name": p["name"], "qty": random.randint(1, 2), "price": p["price"]}
                for p in picks
            ]
            total = sum(l["qty"] * l["price"] for l in lines)
            day = random.randint(1, 16)
            orders.append({
                "id": f"ORD-2026-{n:04d}",
                "customerId": cust_id,          # <- partition key of 'orders'
                "customerName": cust_name,
                "city": city,
                "orderDate": f"2026-11-{day:02d}T{random.randint(8, 22):02d}:{random.randint(0, 59):02d}:00Z",
                "status": random.choice(STATUSES),
                "paymentMode": random.choice(PAYMENTS),
                "items": lines,
                "total": total,
            })
            n += 1
    return orders


# --------------------------------------------------------------------------
# 2. Images and documents
# --------------------------------------------------------------------------
def make_product_label():
    """A slightly tilted, slightly blurry 'phone photo' of a pack label."""
    W, H = 900, 560
    img = Image.new("RGB", (W, H), (238, 232, 220))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, W - 40, H - 40], fill=(255, 253, 245), outline=(120, 80, 40), width=4)
    d.text((70, 70), "TWO BROTHERS ORGANIC FARMS", font=font(FONT_B, 34), fill=(90, 50, 20))
    d.text((70, 125), "Cold-Pressed Groundnut Oil", font=font(FONT_B, 30), fill=(20, 20, 20))
    lines = [
        "Net Quantity: 1 Litre",
        "MRP: Rs. 399.00 (Incl. of all taxes)",
        "Batch No: GN2611B",
        "Mfg. Date: 02/11/2026",
        "Best Before: 01/05/2027",
        "FSSAI Lic. No. 11521998000123",
        "Customer care: 1800-123-4567",
    ]
    y = 190
    for t in lines:
        d.text((70, y), t, font=font(FONT, 26), fill=(30, 30, 30))
        y += 44
    img = img.rotate(2.5, expand=False, fillcolor=(200, 195, 185)).filter(ImageFilter.GaussianBlur(0.6))
    img.save(ASSETS / "product_label.png")


def make_return_note():
    W, H = 900, 520
    img = Image.new("RGB", (W, H), (250, 250, 240))
    d = ImageDraw.Draw(img)
    for y in range(90, H, 52):  # notebook lines
        d.line([(30, y), (W - 30, y)], fill=(180, 200, 230), width=2)
    d.line([(90, 0), (90, H)], fill=(230, 150, 150), width=2)
    hand = font(FONT_HAND, 30)
    text = [
        "Order ID: ORD-2026-0004",
        "Item: Running Shoes Ultraboost",
        "Reason: Size 9 is too tight,",
        "please exchange for size 10.",
        "Name: Rahul Verma  Ph: 98480 12345",
    ]
    y = 50
    for t in text:
        d.text((110 + random.randint(-4, 4), y), t, font=hand, fill=(20, 40, 120))
        y += 52
    img = img.rotate(-1.5, fillcolor=(250, 250, 240))
    img.save(ASSETS / "return_note.png")


def make_receipt():
    W, H = 520, 760
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    m = font(FONT_MONO, 20)
    mb = font(FONT_B, 24)
    y = 30
    for t, f in [("SHOPKART EXPRESS STORE", mb), ("Banjara Hills, Hyderabad", m), ("GSTIN: 36AABCS1234F1Z5", m),
                 ("Tel: 040-2345 6789", m), ("-" * 38, m), ("Date: 14/11/2026   Time: 18:42", m),
                 ("Bill No: SKX-88231", m), ("-" * 38, m)]:
        d.text((30, y), t, font=f, fill="black"); y += 32
    for name, qty, amt in [("Tata Tea Gold 1kg", 1, "560.00"), ("Aashirvaad Atta 10kg", 2, "930.00"),
                           ("Haldiram Bhujia 1kg", 1, "240.00"), ("Milton Bottle 1L", 1, "549.00")]:
        d.text((30, y), f"{name[:22]:<22} x{qty} {amt:>9}", font=m, fill="black"); y += 30
    for t in ["-" * 38, f"{'Subtotal':<27}{'2279.00':>11}", f"{'GST (incl.)':<27}{'0.00':>11}",
              f"{'TOTAL':<27}{'2279.00':>11}", "Paid via UPI", "-" * 38, "Thank you! Visit again"]:
        d.text((30, y), t, font=m, fill="black"); y += 30
    img.save(ASSETS / "receipt_store.png")


def make_invoice_pdf():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(ASSETS / "invoice_technova.pdf"), pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm)
    s = []
    s.append(Paragraph("<b>TechNova Supplies Pvt. Ltd.</b>", styles["Title"]))
    s.append(Paragraph("Plot 42, HITEC City, Hyderabad, Telangana 500081<br/>GSTIN: 36AAACT4321K1Z9 | accounts@technova.example", styles["Normal"]))
    s.append(Spacer(1, 10))
    s.append(Paragraph("<b>TAX INVOICE</b>", styles["Heading2"]))
    meta = [["Invoice No:", "TN-INV-2026-0457", "Invoice Date:", "10/11/2026"],
            ["PO Number:", "SK-PO-7781", "Due Date:", "25/11/2026"]]
    t = Table(meta, colWidths=[30 * mm, 50 * mm, 30 * mm, 40 * mm])
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 10)]))
    s.append(t)
    s.append(Spacer(1, 10))
    s.append(Paragraph("<b>Bill To:</b> ShopKart E-Commerce Pvt. Ltd., Warehouse 3, Shamshabad, Hyderabad 501218", styles["Normal"]))
    s.append(Spacer(1, 12))
    rows = [["#", "Description", "Qty", "Unit Price (Rs.)", "Amount (Rs.)"],
            ["1", "boAt Rockerz 450 Bluetooth Headphones", "50", "1,050.00", "52,500.00"],
            ["2", "Samsung Galaxy M35 5G (8GB/128GB)", "20", "14,200.00", "2,84,000.00"],
            ["3", "USB-C Fast Charger 25W", "100", "450.00", "45,000.00"]]
    t = Table(rows, colWidths=[10 * mm, 80 * mm, 15 * mm, 35 * mm, 35 * mm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ]))
    s.append(t)
    s.append(Spacer(1, 8))
    tot = [["Subtotal", "3,81,500.00"], ["IGST @18%", "68,670.00"], ["Total Amount Due", "Rs. 4,50,170.00"]]
    t = Table(tot, colWidths=[140 * mm, 35 * mm])
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "RIGHT"), ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold")]))
    s.append(t)
    s.append(Spacer(1, 16))
    s.append(Paragraph("Payment terms: Net 15 days. Bank: HDFC Bank, A/c name TechNova Supplies Pvt. Ltd.", styles["Normal"]))
    s.append(Paragraph("This is a computer-generated invoice for training purposes only.", styles["Italic"]))
    doc.build(s)


def make_product_images(products):
    out = ASSETS / "product_images"
    out.mkdir(parents=True, exist_ok=True)
    palette = {"Electronics": (31, 78, 121), "Fashion": (176, 58, 46), "Home & Kitchen": (40, 116, 80),
               "Books": (110, 70, 140), "Grocery": (196, 130, 20)}
    for p in products:
        img = Image.new("RGB", (480, 480), palette[p["category"]])
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([30, 30, 450, 450], 30, outline="white", width=4)
        d.text((60, 70), p["category"].upper(), font=font(FONT_B, 26), fill="white")
        words, line, y = p["name"].split(), "", 180
        for w in words:
            if len(line + w) > 20:
                d.text((60, y), line, font=font(FONT, 28), fill="white"); y += 40; line = ""
            line += w + " "
        d.text((60, y), line, font=font(FONT, 28), fill="white")
        d.text((60, 390), f"Rs. {p['price']:,}", font=font(FONT_B, 30), fill="white")
        img.save(out / f"{p['sku']}.png")


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    products = build_products()
    orders = build_orders(products)
    (DATA / "products.json").write_text(json.dumps(products, indent=2, ensure_ascii=False))
    (DATA / "orders.json").write_text(json.dumps(orders, indent=2, ensure_ascii=False))
    make_product_label()
    make_return_note()
    make_receipt()
    make_invoice_pdf()
    make_product_images(products)
    print(f"Wrote {len(products)} products, {len(orders)} orders and all sample assets.")
