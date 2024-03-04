#!/usr/bin/env python
"""Run the trade bot."""
import logging
import os
import time

from schedule import every, repeat, run_pending

from thetagang_notifications.auth import get_auth_token
from thetagang_notifications.config import PATRON_TRADES_ONLY, SKIPPED_USERS
from thetagang_notifications.notification import get_notifier
from thetagang_notifications.trade import get_trade_class
from thetagang_notifications.trade_queue import TradeQueue

# Setup our shared logger.
log = logging.getLogger(__name__)
log.info("🚀 Running thetagang trades bot")

if PATRON_TRADES_ONLY:
    log.info("Only patron trades will be processed")

if SKIPPED_USERS:
    log.info("The following users will be skipped: %s", SKIPPED_USERS)


@repeat(every(6).hours)
def do_auth():
    """Refresh the authentication token."""
    log.info("🔑 Refreshing authentication token")
    token = get_auth_token()
    with open("/tmp/auth_token", "w", encoding="utf8") as fileh:
        fileh.write(token)
    log.info("✅ Authentication token refreshed")


@repeat(every(60).seconds)
def run_queue():
    """Enqueue the trades which need notifications."""
    log.info("🔎 Checking for new trades")
    tq = TradeQueue()
    tq.update_trades()
    tq.build_queue()
    for queued_trade in tq.queued_trades:
        trade_obj = get_notifier(get_trade_class(queued_trade))
        trade_obj.notify()


if __name__ == "__main__":
    if os.environ.get("DAEMONIZE_TRADE_BOT", False):
        log.info("Running bot as a daemon...")
        do_auth()
        while True:
            run_pending()
            time.sleep(1)
    else:
        log.info("Running as one-shot process...")
        run_queue()
