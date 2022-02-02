#!/usr/bin/env python
"""Set the schedule for running various notification tasks."""
import logging
import time

import schedule

from thetagang_notifications import trends


# Setup our shared logger.
log = logging.getLogger(__name__)
log.info("🚀 thetagang-notifications starting up!")


# Set up simple functions to call the methods in each module.
def notify_for_trends():
    """Notify for new trends."""
    trends.main()


# Schedule the runs of various tasks.
schedule.every(1).minutes.do(notify_for_trends)

for upcoming_job in schedule.get_jobs():
    log.info("⏰ %s", upcoming_job.__repr__())

# Run pending tasks forever.
while True:
    schedule.run_pending()
    time.sleep(1)
