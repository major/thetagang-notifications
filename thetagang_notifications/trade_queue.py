"""Build queues for trade notifications from thetagang.com."""
import dbm
import logging

import requests

from thetagang_notifications import config

log = logging.getLogger(__name__)


def build_queue() -> list:
    """Assemble and return a queue of trades that require notification."""
    queued_trades = [x for x in get_trades() if process_trade(x)]
    log.info("Found %s trades to notify", len(queued_trades))
    return queued_trades


def get_trades() -> list:
    """Get the most recently updated trades."""
    log.info("Getting most recently updated trades")
    params = {"api_key": config.TRADES_API_KEY}
    url = "https://api.thetagang.com/v1/trades"
    resp = requests.get(url, params)

    # Examine the oldest trades first.
    trades = resp.json()["data"]["trades"]
    trades.reverse()

    return trades


def process_trade(trade) -> list:
    """Determine how to handle a trade returned by the API."""
    guid = trade["guid"]

    # Skip any non-patron trades.
    if trade["User"]["role"] != "patron":
        return []

    with dbm.open(f"{config.STORAGE_DIR}/trades.dbm", "c") as db:
        db_state = db.get(guid, None)
        if not db_state or (db_state != trade_status(trade)):
            db[guid] = trade_status(trade)
            return trade

    return []


def trade_status(trade) -> bytes:
    """Determine if trade is open or closed."""
    if trade["close_date"]:
        return b"closed"

    return b"open"
