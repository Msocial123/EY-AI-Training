"""LOAD step: store the transformed data in SQLite and write a run report."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

TABLES = {
    "orders_clean.csv": "fact_orders",
    "rejected_orders.csv": "rejected_orders",
    "category_summary.csv": "daily_category_sales",
    "invoices.csv": "supplier_invoices",
}


def load_to_sqlite(stage_dir, database_path):
    """Load every staged CSV into its SQLite table. Returns {table: row_count}."""
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    row_counts = {}
    connection = sqlite3.connect(database_path)
    try:
        for csv_name, table_name in TABLES.items():
            csv_path = Path(stage_dir) / csv_name
            if not csv_path.exists():
                raise FileNotFoundError(f"Staged file missing: {csv_path}")
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, connection, if_exists="replace", index=False)
            row_counts[table_name] = len(df)
        connection.commit()
    finally:
        connection.close()
    return row_counts


def write_run_report(output_dir, row_counts, status, started_at):
    """Write a small JSON report that tells the team what happened in this run."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    report = {
        "pipeline": "shopease_daily_sales",
        "status": status,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "row_counts": row_counts,
    }
    report_path = Path(output_dir) / "run_report.json"
    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    return report_path
