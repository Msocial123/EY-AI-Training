"""
LAB 1 SOLUTION - Configs (JSON + YAML)

Task:
  1. Read data/flash_sale.yaml with yaml.safe_load
  2. Print the sale name and timings
  3. For every product print MRP, sale price and % saved
  4. Products where sale_price > mrp are a MISTAKE -> list them separately
  5. Save output/flash_sale_report.json with valid deals and mistakes
"""
import json
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent


def main():
    with open(BASE_DIR / "data" / "flash_sale.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    sale = config["sale"]
    print(f"*** {sale['name']} ***  {sale['starts_at']} to {sale['ends_at']}")
    print(f"Limit: {sale['max_units_per_customer']} units per customer\n")

    deals, mistakes = [], []
    for p in config["products"]:
        if p["sale_price"] > p["mrp"]:
            mistakes.append(p)
            continue
        saved = round((p["mrp"] - p["sale_price"]) / p["mrp"] * 100)
        deals.append({**p, "percent_off": saved})
        print(f"{p['name']:<20} MRP {p['mrp']:>5}  NOW {p['sale_price']:>5}  ({saved}% off)")

    for p in mistakes:
        print(f"CHECK CONFIG: {p['name']} sale price {p['sale_price']} > MRP {p['mrp']}")

    out_dir = BASE_DIR / "output"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "flash_sale_report.json", "w", encoding="utf-8") as f:
        json.dump({"sale": sale["name"], "deals": deals, "mistakes": mistakes}, f, indent=2)
    print("\nSaved output/flash_sale_report.json")


if __name__ == "__main__":
    main()
