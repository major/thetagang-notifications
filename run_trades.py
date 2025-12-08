#!/usr/bin/env python
"""Run the trade bot."""

import atexit
import gc
import logging
import os
import signal
import sys
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

# 🔧 Create TradeQueue ONCE and reuse to avoid connection leaks
trade_queue: TradeQueue | None = None


def get_trade_queue() -> TradeQueue:
    """Get or create the singleton TradeQueue instance."""
    global trade_queue
    if trade_queue is None:
        log.info("📡 Creating TradeQueue with persistent connections")
        trade_queue = TradeQueue()
    return trade_queue


def cleanup() -> None:
    """Clean up resources on shutdown."""
    global trade_queue
    if trade_queue is not None:
        log.info("🧹 Cleaning up TradeQueue resources")
        trade_queue.close()
        trade_queue = None


def signal_handler(signum: int, frame: object) -> None:
    """Handle shutdown signals gracefully."""
    log.info("🛑 Received signal %s, shutting down...", signum)
    cleanup()
    sys.exit(0)


# Register cleanup handlers
atexit.register(cleanup)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


@repeat(every(15).seconds)
def run_queue() -> None:
    """Enqueue the trades which need notifications."""
    log.info("🔎 Checking for new trades")
    tq = get_trade_queue()
    tq.update_trades()
    for queued_trade in tq.build_queue():
        trade_obj = get_notifier(get_trade_class(queued_trade))
        trade_obj.notify()
    log.info("👍 Done processing trades")

    # 🔧 Force garbage collection to clean up circular refs between Trade/Notification
    gc.collect()


if __name__ == "__main__":
    if os.environ.get("DAEMONIZE_TRADE_BOT", False):
        log.info("Running bot as a daemon...")
        while True:
            run_pending()
            time.sleep(1)
    else:
        log.info("Running as one-shot process...")
        run_queue()
        cleanup()
