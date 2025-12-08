"""Build queues for trade notifications from thetagang.com."""

import logging
from datetime import datetime, timedelta, timezone

import httpx
from dateutil import parser
from redis import Redis

from thetagang_notifications.config import settings

log = logging.getLogger(__name__)


class TradeQueue:
    """Set up a queue of trades to work through.

    This class is designed to be instantiated once and reused across iterations
    to avoid memory leaks from repeated Redis/HTTP connection creation.
    """

    def __init__(self) -> None:
        """Constructor for TradeQueue."""
        self.db_conn = Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
        self.skipped_users = settings.skipped_users_list
        self.latest_trades: list = []
        # 🔧 Create a persistent HTTP client to avoid connection pool leaks
        self._http_client = httpx.Client(timeout=15)

    def close(self) -> None:
        """Clean up resources - call when shutting down."""
        self._http_client.close()
        self.db_conn.close()

    def update_trades(self) -> list:
        """Get the most recently updated trades."""
        headers: dict[str, str] = {"Authorization": settings.trades_api_key}
        url = "https://api3.thetagang.com/api/patrons"
        resp = self._http_client.get(url, headers=headers)

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
            and x["User"]["role"] in ["patron", "joonie"]
            and x["mistake"] is not True
        ]
        log.info("Found %s valid trades", len(valid_trades))
        return [x for x in valid_trades if self.process_trade(x)]

    def process_trade(self, trade: dict) -> dict | None:
        """Determine how to handle a trade returned by the API.

        We're looking for a trade that we haven't seen before, and if we haven't seen it
        before, then it shouldn't be an old trade. If we have seen it before, then we
        only alert on it if it changed status, such as opened to closed.
        """
        if not self.trade_exists(trade):
            # We haven't seen this trade before.
            if not self.trade_is_old(trade):
                # This trade isn't a old trade from long ago.
                self.store_trade(trade)
                return trade

        elif self.trade_has_new_status(trade):
            # We've seen this trade before, but it has a new status.
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

    def trade_is_old(self, trade: dict) -> bool:
        """Detect when a new trade appears, but it is actually really old.

        This situation happens when the website does a database migration and the
        updated_at column is updated to today's date. It causes the bot to think that
        the trade is a new one, but it could be weeks, months, or years old.
        """
        updated_at = parser.parse(trade["updatedAt"])
        day_ago = datetime.now(timezone.utc) - timedelta(days=1)

        return updated_at < day_ago

    def trade_status(self, trade: dict) -> str:
        """Determine if trade is open or closed."""
        return "closed" if trade["close_date"] else "open"
