"""Build queues for trade notifications from thetagang.com."""

import logging

import httpx
from redis import Redis

from thetagang_notifications.config import REDIS_HOST, REDIS_PORT, SKIPPED_USERS, TRADES_API_KEY

log = logging.getLogger(__name__)


class TradeQueue:
    """Set up a queue of trades to work through."""

    def __init__(self) -> None:
        """Constructor for TradeQueue."""
        self.db_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.skipped_users = SKIPPED_USERS
        self.latest_trades: list = []

    def update_trades(self) -> list:
        """Get the most recently updated trades."""
        log.info("Getting most recently updated trades...")

        headers = {"Authorization": TRADES_API_KEY}
        url = "https://api3.thetagang.com/api/patrons"
        resp = httpx.get(url, headers=headers, timeout=15)

        self.latest_trades = resp.json()["data"]

        # Ensure we always have the latest trades first
        self.latest_trades.reverse()

        return list(self.latest_trades)

    def build_queue(self) -> list:
        """Assemble a queue of trades to process.

        Returns:
            list: Trades in the queue to be processed.
        """
        valid_trades = [
            x
            for x in self.latest_trades
            if x["User"]["username"] not in self.skipped_users
            and x["User"]["role"] in ("patron", "joonie")
            and x["mistake"] is False
        ]
        return [x for x in valid_trades if self.process_trade(x)]

    def process_trade(self, trade: dict) -> dict | None:
        """Determine how to handle a trade returned by the API."""
        if not self.trade_exists(trade) or self.trade_has_new_status(trade):
            self.store_trade(trade)
            return trade

        return None

    def store_trade(self, trade: dict) -> None:
        """Store a trade in the database."""
        self.db_conn.set(trade["guid"], self.trade_status(trade))

    def trade_exists(self, trade: dict) -> bool:
        """Check if a trade exists in the database."""
        return bool(self.db_conn.exists(trade["guid"]))

    def trade_has_new_status(self, trade: dict) -> bool:
        """Determine if the trade has a new status."""
        return self.db_conn.get(trade["guid"]) != self.trade_status(trade)

    def trade_status(self, trade: dict) -> str:
        """Determine if trade is open or closed."""
        return "closed" if trade["close_date"] else "open"
