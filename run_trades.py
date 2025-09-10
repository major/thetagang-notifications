#!/usr/bin/env python
"""Run the trade bot."""

import logging
import os
import time

from schedule import every, repeat, run_pending

from thetagang_notifications.config import settings
from thetagang_notifications.notification import get_notifier
from thetagang_notifications.trade import get_trade_class
from thetagang_notifications.trade_queue import TradeQueue

SKIPPED_USERS = settings.skipped_users

# Setup our shared logger.
log = logging.getLogger(__name__)
log.info("🚀 Running thetagang trades bot")

if SKIPPED_USERS:
    log.info("The following users will be skipped: %s", SKIPPED_USERS)


@repeat(every(15).seconds)
def run_queue() -> None:
    """Enqueue the trades which need notifications."""
    log.info("🔎 Checking for new trades")
    tq = TradeQueue()
    tq.update_trades()
    for queued_trade in tq.build_queue():
        trade_obj = get_notifier(get_trade_class(queued_trade))
        trade_obj.notify()
    log.info("👍 Done processing trades")


if __name__ == "__main__":
    if os.environ.get("DAEMONIZE_TRADE_BOT", False):
        log.info("Running bot as a daemon...")
        while True:
            run_pending()
            time.sleep(1)
    else:
        log.info("Running as one-shot process...")
        run_queue()
