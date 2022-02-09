#!/usr/bin/env python
"""Set the schedule for running various notification tasks."""
import logging
import time

from schedule import every, get_jobs, repeat, run_all, run_pending

from thetagang_notifications import earnings, trends, trades


# Setup our shared logger.
log = logging.getLogger(__name__)
log.info("🚀 thetagang-notifications starting up!")


@repeat(every(1).minutes.at(":00"))
def notify_for_trends():
    """Notify for new trends."""
    trends.main()


@repeat(every(1).minutes.at(":30"))
def notify_for_trades():
    """Notify for new trades."""
    trades.main()


# Start earnings notifications via Tweepy's stream thread.
earnings.main()

# Dump all the jobs to the log on startup.
for upcoming_job in get_jobs():
    log.info("⏰ %s", upcoming_job.__repr__())

# Run all of the jobs right now
run_all()

# Run pending tasks forever.
while True:
    run_pending()
    time.sleep(1)
