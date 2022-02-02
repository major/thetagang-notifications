#!/usr/bin/env python
"""Set the schedule for running various notification tasks."""
import logging
import time

from schedule import every, get_jobs, repeat, run_pending

from thetagang_notifications import trends


# Setup our shared logger.
log = logging.getLogger(__name__)
log.info("🚀 thetagang-notifications starting up!")


@repeat(every(5).minutes.at(":00"))
def notify_for_trends():
    """Notify for new trends."""
    trends.main()


# Dump all the jobs to the log on startup.
for upcoming_job in get_jobs():
    log.info("⏰ %s", upcoming_job.__repr__())

# Run pending tasks forever.
while True:
    run_pending()
    time.sleep(1)
