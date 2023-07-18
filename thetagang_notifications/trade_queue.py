"""Build queues for trade notifications from thetagang.com."""
import logging

import redis
import requests

from thetagang_notifications.config import PATRON_TRADES_ONLY, SKIPPED_USERS, TRADES_API_KEY

log = logging.getLogger(__name__)


def build_queue() -> list:
    """Assemble and return a queue of trades that require notification."""
    queued_trades = [x for x in get_trades() if process_trade(x)]
    log.info("Trades to notify: %s", len(queued_trades))
    return queued_trades


def get_trades() -> list:
    """Get the most recently updated trades."""
    log.info("Getting most recently updated trades...")
    params = {"api_key": TRADES_API_KEY}
    url = "https://api.thetagang.com/v1/trades"
    resp = requests.get(url, params, timeout=15)

    # Get a list of trades.
    trades = resp.json()["data"]["trades"]

    # Remove any non-patron trades.
    if PATRON_TRADES_ONLY:
        trades = [x for x in trades if x["User"]["role"] == "patron"]

    # Remove any trades from skipped users.
    if [""] != SKIPPED_USERS:
        trades = [x for x in trades if x["User"]["username"] not in SKIPPED_USERS]

    # Reverse the order so we examine the oldest trades first.
    trades.reverse()
    log.info("Trades to process: %s", len(trades))

    return trades


def process_trade(trade) -> list:
    """Determine how to handle a trade returned by the API."""
    guid = trade["guid"]

    db_state = retrieve_trade(guid)
    print(f"Trade {guid} is {trade_status(trade)}")
    if not db_state or (db_state != trade_status(trade)):
        store_trade(guid, trade_status(trade))
        return trade

    return []


def retrieve_trade(guid) -> str | None:
    """Get a trade from the redis database."""
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    return r.get(guid)


def store_trade(guid, trade_status) -> bool:
    """Get a trade from the redis database."""
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    print("storing trade!")
    return r.set(guid, trade_status)


def trade_status(trade) -> bytes:
    """Determine if trade is open or closed."""
    if trade["close_date"]:
        return b"closed"

    return b"open"
