"""
Weekly automated report scheduler.
Runs every Monday at 9:00 AM.

Usage:
python reports/scheduler.py
"""

import os
import sys
import subprocess
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.blocking import BlockingScheduler

# Project root
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

# Logging
logging.basicConfig(
    filename="scheduler.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

scheduler = BlockingScheduler()


def run_script(script_path):
    """
    Run a python script and raise exception if it fails.
    """
    subprocess.run(
        [sys.executable, script_path],
        check=True
    )


def run_weekly_report():

    start_time = datetime.now()

    print("\n" + "=" * 60)
    print(f"Running Weekly Report : {start_time}")
    print("=" * 60)

    logging.info("Weekly report started")

    try:

        print("Step 1: Topic Clustering")
        run_script("analysis/clustering.py")

        print("Step 2: AI Insights")
        run_script("analysis/ai.py")

        print("Step 3: Report Generation")
        run_script("reports/generator.py")

        end_time = datetime.now()
        runtime = (end_time - start_time).total_seconds()

        print(f"\nReport generated successfully")
        print(f"Runtime: {runtime:.2f} seconds")

        logging.info(
            f"Weekly report completed successfully "
            f"in {runtime:.2f} seconds"
        )

    except subprocess.CalledProcessError as e:

        print(f"\nReport generation failed")
        print(e)

        logging.error(f"Weekly report failed: {e}")


@scheduler.scheduled_job(
    "cron",
    day_of_week="mon",
    hour=9,
    minute=0,
    max_instances=1
)
def scheduled_job():
    run_weekly_report()


if __name__ == "__main__":

    print("Weekly Report Scheduler Started")
    print("Runs every Monday at 9:00 AM")
    print("Press Ctrl+C to stop\n")

    # Uncomment for testing
    # run_weekly_report()
try:
    scheduler.start()

except (KeyboardInterrupt, SystemExit):
    print("\nStopping scheduler...")
    scheduler.shutdown()
    print("Scheduler stopped.")