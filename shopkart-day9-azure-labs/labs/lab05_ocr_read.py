"""
LAB 5 - Introduction to OCR with Azure AI Vision (Read)
=======================================================
Curriculum topic : "Introduction to OCR"

OCR = Optical Character Recognition = turning PIXELS of text into TEXT you can
search, store and validate.

ShopKart use cases in this lab
  A) Seller onboarding: a seller uploads a PHOTO of the product label.
     We OCR it, pull out MRP / batch / expiry / FSSAI number and check that the
     MRP on the label matches the price the seller typed in the listing.
     (Legal Metrology rules: you cannot sell above MRP.)
  B) Returns desk: customer uploads a photo of a HANDWRITTEN return note.
     We OCR it, find the Order ID + phone, and create a return request.
     Low-confidence words go to a human for checking.

Which OCR engine? (both use Microsoft's same "Read" OCR technology)
  1. Document Intelligence 'prebuilt-read'  -> used if DOCINTEL_* keys are set (RECOMMENDED:
     Microsoft's migration guidance points OCR workloads here; Image Analysis retires Sept 2028)
  2. Azure AI Vision Image Analysis READ    -> used if only VISION_* keys are set
  3. OFFLINE                                -> no keys: uses sample_outputs/*.json (same JSON shape
                                               Azure returns) so everyone can practise the PARSING logic

Run:  python labs/lab05_ocr_read.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import config  # noqa: E402
from common.clients import docintel_client, vision_client  # noqa: E402
from common.pretty import banner, step, info, ok, warn, fail, table  # noqa: E402

CONFIDENCE_THRESHOLD = 0.80   # below this -> ask a human to verify


# ------------------------------------------------------------------ OCR call --
def ocr_image(image_path: Path, sample_name: str) -> dict:
    """Returns OCR output in ONE common shape: {"readResult": {"blocks": [{"lines": [...]}]}}"""
    di = docintel_client()
    if di is not None:
        info(f"ONLINE: Document Intelligence 'prebuilt-read' on {image_path.name} ...")
        with open(image_path, "rb") as f:
            result = di.begin_analyze_document("prebuilt-read", body=f).result()
        data = normalise_docintel(result.as_dict())
        _save_live(data, sample_name)
        return data

    vision = vision_client()
    if vision is not None:
        from azure.ai.vision.imageanalysis.models import VisualFeatures
        info(f"ONLINE: Azure AI Vision READ on {image_path.name} ({image_path.stat().st_size // 1024} KB) ...")
        result = vision.analyze(image_data=image_path.read_bytes(), visual_features=[VisualFeatures.READ])
        data = result.as_dict()
        _save_live(data, sample_name)
        return data

    warn(f"OFFLINE mode: loading sample_outputs/{sample_name}.json")
    return json.loads((config.SAMPLE_OUTPUTS_DIR / f"{sample_name}.json").read_text())


def _save_live(data: dict, sample_name: str) -> None:
    out = config.SAMPLE_OUTPUTS_DIR / f"{sample_name}.live.json"
    out.write_text(json.dumps(data, indent=1, default=str))
    ok(f"saved raw response to {out.relative_to(config.ROOT)}")


def normalise_docintel(result: dict) -> dict:
    """Document Intelligence returns pages -> lines/words linked by character spans.
    Convert it to the Vision-style blocks -> lines -> words shape used below."""
    lines_out = []
    for page in result.get("pages", []):
        words = page.get("words", [])
        for line in page.get("lines", []):
            span = (line.get("spans") or [{"offset": 0, "length": 0}])[0]
            start, end = span["offset"], span["offset"] + span["length"]
            line_words = [w for w in words if start <= w["span"]["offset"] < end]
            poly = line.get("polygon") or [0, 0]
            lines_out.append({
                "text": line["content"],
                "boundingPolygon": [{"x": round(poly[0]), "y": round(poly[1])}],
                "words": [{"text": w["content"], "confidence": w.get("confidence", 1.0)} for w in line_words],
            })
    return {"readResult": {"blocks": [{"lines": lines_out}]}}


def lines_from(result: dict) -> list[dict]:
    """Flatten blocks -> lines and compute the weakest word confidence per line."""
    lines = []
    for block in result.get("readResult", {}).get("blocks", []):
        for line in block.get("lines", []):
            confs = [w.get("confidence", 1.0) for w in line.get("words", [])]
            lines.append({
                "text": line["text"],
                "min_conf": round(min(confs), 3) if confs else None,
                "top_left": f"({line['boundingPolygon'][0]['x']},{line['boundingPolygon'][0]['y']})",
            })
    return lines


# ---------------------------------------------------- Use case A: product label --
LABEL_PATTERNS = {
    "mrp": r"MRP[:\s]*Rs\.?\s*([\d,]+(?:\.\d{2})?)",
    "batch": r"Batch\s*No[:.\s]*([A-Z0-9]+)",
    "mfg_date": r"Mfg\.?\s*Date[:\s]*(\d{2}/\d{2}/\d{4})",
    "best_before": r"Best\s*Before[:\s]*(\d{2}/\d{2}/\d{4})",
    "fssai": r"FSSAI\s*Lic\.?\s*No\.?\s*(\d{14})",
}


def product_label_demo():
    step("A) Seller uploaded a photo of the groundnut-oil label (assets/product_label.png)")
    result = ocr_image(config.ASSETS_DIR / "product_label.png", "ocr_product_label")
    lines = lines_from(result)
    table(lines)

    full_text = "\n".join(l["text"] for l in lines)
    extracted = {}
    for field, pattern in LABEL_PATTERNS.items():
        m = re.search(pattern, full_text, re.IGNORECASE)
        extracted[field] = m.group(1) if m else None
    step("Structured fields pulled out with regex:")
    for k, v in extracted.items():
        (ok if v else fail)(f"{k:12} = {v}")

    step("Business rule: listing price must not exceed MRP on the label")
    catalogue = {p["sku"]: p for p in json.loads((config.DATA_DIR / "products.json").read_text())}
    listing_price = catalogue["GROC-5003"]["price"]
    mrp = float(extracted["mrp"].replace(",", "")) if extracted["mrp"] else None
    info(f"Seller's listing price: Rs.{listing_price}   |   MRP on label: Rs.{mrp}")
    if mrp is None:
        fail("MRP not found -> send to manual review")
    elif listing_price <= mrp:
        ok("APPROVED - listing price is within MRP")
    else:
        fail("REJECTED - price above MRP is illegal")


# ---------------------------------------------------- Use case B: return note --
def return_note_demo():
    step("B) Customer uploaded a handwritten return note (assets/return_note.png)")
    result = ocr_image(config.ASSETS_DIR / "return_note.png", "ocr_return_note")
    lines = lines_from(result)
    table(lines)

    text = " ".join(l["text"] for l in lines)
    order_id = re.search(r"ORD-\d{4}-\d{4}", text)
    phone = re.search(r"(\d{5}\s?\d{5})", text)
    reason = re.search(r"Reason:\s*(.+?)(?:Name:|$)", text)
    request = {
        "orderId": order_id.group(0) if order_id else None,
        "phone": phone.group(1).replace(" ", "") if phone else None,
        "reason": reason.group(1).strip() if reason else None,
    }
    step("Return request built from OCR:")
    for k, v in request.items():
        info(f"{k:8} = {v}")

    orders = {o["id"]: o for o in json.loads((config.DATA_DIR / "orders.json").read_text())}
    if request["orderId"] in orders:
        o = orders[request["orderId"]]
        ok(f"Order found: {o['customerName']}, status={o['status']}, total=Rs.{o['total']:,}")
    else:
        fail("Order ID not found -> ask customer to re-upload")

    shaky = [l for l in lines if l["min_conf"] is not None and l["min_conf"] < CONFIDENCE_THRESHOLD]
    if shaky:
        warn(f"{len(shaky)} line(s) below confidence {CONFIDENCE_THRESHOLD} -> human review queue:")
        for l in shaky:
            info(f"   '{l['text']}'  (lowest word confidence {l['min_conf']})")
    else:
        ok("All lines above confidence threshold - auto-approve")


def main():
    banner("LAB 5 - OCR with Azure AI Vision Read")
    product_label_demo()
    return_note_demo()
    banner("LAB 5 complete - OCR gives TEXT; Document Intelligence (lab 6) gives FIELDS")


if __name__ == "__main__":
    main()
