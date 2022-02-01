#!/usr/bin/env python
import logging
import time


import schedule


from thetagang_notifications import trends

# Setup our shared logger.
log = logging.getLogger(__name__)

# Schedule the runs of various tasks.
schedule.every(5).minutes.do(trends.main())

# Run pending tasks forever.
while True:
    schedule.run_pending()
    time.sleep(1)
