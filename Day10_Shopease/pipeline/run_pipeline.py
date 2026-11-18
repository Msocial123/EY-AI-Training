"""Orchestrator: runs Extract -> Transform -> Load with logging and error handling.

Examples (run from the project folder):
    python -m pipeline.run_pipeline
    python -m pipeline.run_pipeline --stage transform --input data/raw --output data/staging
    python -m pipeline.run_pipeline --stage load --input data/staging --output data/processed
"""
import argparse
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from pipeline.config import load_settings, resolve_path
from pipeline.extract import extract_invoices, extract_orders
from pipeline.load import load_to_sqlite, write_run_report
from pipeline.logger import get_logger
from pipeline.storage import upload_to_blob
from pipeline.transform import (add_order_totals, build_category_summary,
                                clean_orders, validate_invoices)


def run_transform_stage(input_dir, stage_dir, settings, logger):
    """Extract raw files, transform them and save the results as staged CSV files."""
    stage_dir = Path(stage_dir)
    raw_orders = extract_orders(input_dir, settings["orders_file_pattern"])
    logger.info("Extracted %d raw order rows", len(raw_orders))
    invoices = extract_invoices(Path(input_dir) / "invoices")
    logger.info("Extracted %d invoices from PDF files", len(invoices))

    clean, rejected = clean_orders(raw_orders, settings["valid_statuses"])
    logger.info("Clean orders: %d | Rejected orders: %d", len(clean), len(rejected))
    orders = add_order_totals(clean, settings["gst_rate"])
    summary = build_category_summary(orders)
    invoices = validate_invoices(invoices)
    bad_invoices = int((~invoices["is_valid"]).sum())
    if bad_invoices:
        logger.warning("%d invoice(s) failed the subtotal + tax = total check", bad_invoices)

    stage_dir.mkdir(parents=True, exist_ok=True)
    orders.to_csv(stage_dir / "orders_clean.csv", index=False)
    rejected.to_csv(stage_dir / "rejected_orders.csv", index=False)
    summary.to_csv(stage_dir / "category_summary.csv", index=False)
    invoices.to_csv(stage_dir / "invoices.csv", index=False)
    logger.info("Staged files written to %s", stage_dir)


def run_load_stage(stage_dir, output_dir, database_path, logger):
    """Load staged CSV files into SQLite and publish the summary report."""
    row_counts = load_to_sqlite(stage_dir, database_path)
    logger.info("Loaded tables: %s", row_counts)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(stage_dir) / "category_summary.csv", output_dir / "category_summary.csv")
    return row_counts


def parse_args(argv=None):
    """Read command-line options. --input/--output are required for single stages."""
    parser = argparse.ArgumentParser(description="ShopEase daily sales data pipeline")
    parser.add_argument("--stage", choices=["all", "transform", "load"], default="all")
    parser.add_argument("--input", help="Input folder (default: raw_dir in settings.json)")
    parser.add_argument("--output", help="Output folder (default: processed_dir)")
    args = parser.parse_args(argv)
    if args.stage != "all" and not (args.input and args.output):
        parser.error("--input and --output are required with --stage transform/load")
    return args


def main(argv=None):
    """Run the requested stage(s). Returns an exit code: 0 = success, 1 = failure."""
    args = parse_args(argv)
    settings = load_settings()
    logger = get_logger(resolve_path(settings["log_dir"]))
    input_dir = Path(args.input) if args.input else resolve_path(settings["raw_dir"])
    output_dir = Path(args.output) if args.output else resolve_path(settings["processed_dir"])
    started_at = datetime.now()
    timer_start = time.perf_counter()
    row_counts, status = {}, "FAILED"
    logger.info("Pipeline started | stage=%s | input=%s", args.stage, input_dir)

    try:
        if args.stage == "transform":
            run_transform_stage(input_dir, output_dir, settings, logger)
        elif args.stage == "load":
            row_counts = run_load_stage(input_dir, output_dir, output_dir / "shopease.db", logger)
        else:
            staging_dir = resolve_path(settings["staging_dir"])
            run_transform_stage(input_dir, staging_dir, settings, logger)
            row_counts = run_load_stage(staging_dir, output_dir,
                                        resolve_path(settings["database_path"]), logger)
        status = "SUCCESS"
    except Exception as error:
        logger.exception("Pipeline failed: %s", error)

    report_path = write_run_report(output_dir, row_counts, status, started_at)
    logger.info("Pipeline %s in %.2f s | report: %s",
                status, time.perf_counter() - timer_start, report_path)
    if status == "SUCCESS" and args.stage != "transform":
        upload_to_blob(output_dir, settings["blob_container"], logger)
    return 0 if status == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
