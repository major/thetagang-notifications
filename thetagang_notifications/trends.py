"""Handle trades on thetagang.com."""
from functools import cached_property
import logging

from discord_webhook import DiscordWebhook, DiscordEmbed
import requests
from sqlitedict import SqliteDict

from thetagang_notifications import config, utils


log = logging.getLogger(__name__)


class Trend:
    """Class for handling new trending symbols that appear on thetagang.com."""

    def __init__(self, symbol=None):
        """Initialize the basics of the class."""
        self.symbol = symbol
        self.initialize_db()

    @property
    def discord_description(self):
        """Generate a description for Discord notifications."""
        fvz = self.finviz

        # Skip this if we didn't get information from Finviz.
        if fvz is None:
            return ""

        return (
            f"{fvz['Company']}\n"
            f"{fvz['Sector']} - {fvz['Industry']}\n"
            f"{'Earnings: ' + fvz['Earnings'] if fvz['Earnings'] != '-' else ''}"
        )

    @property
    def discord_title(self):
        """Set a title for the Discord message."""
        return f"{self.symbol} added to trending tickers"

    @cached_property
    def finviz(self):
        """Get data from finviz.com about our trending symbol."""
        return utils.get_finviz_stock(self.symbol)

    @classmethod
    def flush_db(cls):
        """Flush all the trends from the database."""
        db = SqliteDict(config.TRENDS_DB, autocommit=True)
        db["trends"] = []
        return True

    def initialize_db(self):
        """Ensure the database is initialized."""
        self.db = SqliteDict(config.TRENDS_DB, autocommit=True, tablename="trends")

        if "trends" not in self.db.keys():
            self.db["trends"] = []

    @property
    def is_new(self):
        """Determine if the trend is new."""
        return self.symbol not in self.db["trends"]

    @property
    def logo(self):
        """Get the stock logo."""
        return utils.get_stock_logo(self.symbol)

    def notify(self):
        """Send notification to Discord."""
        # Exit early if we saw this ticker before, or if Finviz has no data about it.
        if not self.is_new or self.finviz is None:
            return None

        webhook = DiscordWebhook(
            url=config.WEBHOOK_URL_TRENDS,
            rate_limit_retry=True,
            username=config.DISCORD_USERNAME,
        )
        webhook.add_embed(self.prepare_embed())
        result = webhook.execute()

        self.save()
        return result

    def prepare_embed(self):
        """Prepare the webhook embed data."""
        embed = DiscordEmbed(
            title=self.discord_title,
            color="AFE1AF",
            description=self.discord_description,
        )
        embed.set_image(url=self.stock_chart)
        embed.set_thumbnail(url=self.logo)
        return embed

    def save(self):
        """Add the trending ticker to the list of seen trending tickers."""
        self.db["trends"] = self.db["trends"] + [self.symbol]

    @property
    def stock_chart(self):
        """Get the URL to a stock chart for the symbol."""
        return utils.get_stock_chart(self.symbol)


def download_trends():
    """Get latest trends from thetagang.com."""
    resp = requests.get(config.TRENDS_JSON_URL)
    trades_json = resp.json()
    return trades_json["data"]["trends"]


def main():
    """Handle updates for trends."""
    downloaded_trends = download_trends()
    for downloaded_trend in downloaded_trends:
        trend = Trend(downloaded_trend)
        trend.notify()

    if not download_trends:
        Trend.flush_db()


if __name__ == "__main__":  # pragma: no cover
    main()
