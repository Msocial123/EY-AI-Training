"""Runs the pipeline automatically on a schedule using the `schedule` library.

    python -m scheduler.schedule_runner              # every day at schedule_time
    python -m scheduler.schedule_runner --demo       # every 10 seconds (classroom demo)
    python -m scheduler.schedule_runner --run-now    # run once now, then keep the schedule
"""
import argparse
import time

import schedule

from pipeline.config import load_settings, resolve_path
from pipeline.logger import get_logger
from pipeline.run_pipeline import main as run_pipeline


def pipeline_job(logger):
    """The job the scheduler calls. A failed run is logged but never stops the scheduler."""
    logger.info("Scheduler triggered a pipeline run")
    exit_code = run_pipeline([])
    if exit_code != 0:
        logger.error("Scheduled run failed - see the error above")


def start_scheduler(demo=False, run_now=False):
    """Register the job, then loop forever checking whether it is time to run."""
    settings = load_settings()
    logger = get_logger(resolve_path(settings["log_dir"]))
    if demo:
        schedule.every(10).seconds.do(pipeline_job, logger)
        logger.info("DEMO mode: pipeline runs every 10 seconds (Ctrl+C to stop)")
    else:
        schedule.every().day.at(settings["schedule_time"]).do(pipeline_job, logger)
        logger.info("Pipeline scheduled every day at %s", settings["schedule_time"])
    if run_now:
        pipeline_job(logger)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Schedule the ShopEase pipeline")
    parser.add_argument("--demo", action="store_true", help="run every 10 seconds")
    parser.add_argument("--run-now", action="store_true", help="run once immediately")
    options = parser.parse_args()
    start_scheduler(demo=options.demo, run_now=options.run_now)
