"""Handle trades on thetagang.com."""
from functools import cached_property
from datetime import datetime
import logging
import yaml

from dateutil import parser
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests
from sqlitedict import SqliteDict

from thetagang_notifications import config, utils


log = logging.getLogger(__name__)

# The sqlitedict module likes to log a lot at the INFO level. 🥵
sqlite_logger = logging.getLogger("sqlitedict")
sqlite_logger.setLevel(logging.WARNING)

# Earnings notification colors.
COLOR_TRADE_BEARISH = "FD3A4A"
COLOR_TRADE_NEUTRAL = "BFAFB2"
COLOR_TRADE_BULLISH = "299617"


class Trade:
    """Class for handling new trades opened on thetagang.com."""

    def __init__(self, trade):
        """Initialize the basics of the class."""
        self.trade = trade
        self.initialize_db()

    @property
    def breakeven(self):
        """Return the breakeven on a cash secured or naked put."""
        match self.trade_type:
            case "CASH SECURED PUT":
                strike = self.trade["short_put"]
                breakeven = float(strike) - self.trade["price_filled"]
            case "COVERED CALL" | "SHORT NAKED CALL":
                strike = self.trade["short_call"]
                breakeven = float(strike) + self.trade["price_filled"]
            case _:
                return None

        return "{:,.2f}".format(breakeven)

    @property
    def discord_color(self):
        """Set a color for the discord message based on sentiment."""
        match self.sentiment:
            case "bearish":
                return COLOR_TRADE_BEARISH
            case "neutral":
                return COLOR_TRADE_NEUTRAL
            case _:
                return COLOR_TRADE_BULLISH

    @property
    def discord_title(self):
        """Generate a title for discord messages."""
        title = f"{self.symbol}: {self.trade_type}\n"
        if self.is_option_trade and self.is_single_option:
            # We have a long/short single leg trade.
            title += self.get_discord_title_single_leg()
        elif self.is_option_trade and not self.is_single_option:
            # We have a multiple leg option trade, like a spread.
            title += self.get_discord_title_multiple_leg()
        else:
            # If we made it this far, then we have a stock buy/sell.
            title += self.get_discord_title_stock()

        return title

    @property
    def discord_description(self):
        """Generate a footer to end the description."""
        links = (
            f"[{self.username}](https://thetagang.com/{self.username}) | "
            f"[TG: Trade]({self.trade_url}) | "
            f"[TG: {self.symbol}](https://thetagang.com/symbols/{self.symbol}) | "
            f"[Finviz](https://finviz.com/quote.ashx?t={self.symbol})"
        )

        return self.discord_stats_single_leg + links

    @property
    def discord_stats_single_leg(self):
        """Generate stats for a single leg option."""
        # Only support single leg *short* options right now.
        if self.is_single_option and self.is_short:
            return (
                f"${self.breakeven} breakeven\n"
                f"{self.short_return}% potential return "
                f"({self.short_return_annualized}% annualized)\n"
            )

        return ""

    def get_discord_title_single_leg(self):
        """Generate Discord title for a single leg option trade."""
        strike_suffix = "p" if "PUT" in self.trade_type else "c"
        return (
            f"{self.quantity} x {self.pretty_expiration} "
            f"${self.strike}{strike_suffix} for {self.pretty_premium}"
        )

    def get_discord_title_multiple_leg(self):
        """Generate a discord title for a multiple leg option trade."""
        return (
            f"{self.quantity} x {self.pretty_expiration} "
            f"{self.raw_strikes} for {self.pretty_premium}"
        )

    def get_discord_title_stock(self):
        """Generate a Discord title for a stock transaction."""
        return f"{self.quantity} share(s) at {self.pretty_premium}"

    @property
    def dte(self):
        """Calculate days to expiry (DTE) for a trade."""
        # Add one extra day to ensure our current day is included in the total. This
        # avoids dividing by zero and also ensures that we calculate DTE just as
        # thetagang.com does. 😉
        return (self.parse_expiration() - datetime.now()).days + 1

    def initialize_db(self):
        """Ensure the database is initialized."""
        self.db = SqliteDict(config.MAIN_DB, autocommit=True, tablename="trades")

        if "trades" not in self.db.keys():
            self.db["trades"] = []

    @property
    def is_new(self):
        """Determine if the trend is new."""
        return self.guid not in self.db["trades"]

    @property
    def is_option_trade(self):
        """Determine if the trade is an options trade."""
        return self.trade_spec["option_trade"]

    @property
    def is_patron_trade(self):
        """Determine if the trade was made by a patron."""
        return True if self.trade["User"]["role"] == "patron" else False

    @property
    def is_short(self):
        """Determine if the options trade is short or long."""
        return self.trade_spec["short"]

    @property
    def is_single_option(self):
        """Determine if the trade is a single option trade."""
        return self.trade_spec["single_option"]

    def notify(self):
        """Send notification to Discord."""
        if not self.is_patron_trade:
            log.info("👎 Skipping non-patron trade: %s", self.trade_url)
            return None

        if not self.is_new:
            log.info("👀 Already saw patron trade: %s", self.trade_url)
            return None

        webhook = DiscordWebhook(
            url=config.WEBHOOK_URL_TRADES,
            rate_limit_retry=True,
            username=config.DISCORD_USERNAME,
        )
        webhook.add_embed(self.prepare_embed())
        webhook.execute()

        # Record this trade so we don't alert for it again.
        self.save()

        return webhook

    def prepare_embed(self):
        """Prepare the webhook embed data."""
        embed = DiscordEmbed(
            title=self.discord_title,
            color=self.discord_color,
            description=self.discord_description,
        )

        embed.set_image(url=self.symbol_chart)
        embed.set_thumbnail(url=self.symbol_logo)
        embed.set_footer(text=f"{self.username}: {self.trade['note']}")
        return embed

    def parse_expiration(self):
        """Convert JSON expiration date into Python date object."""
        if not self.is_option_trade:
            return None

        return parser.parse(self.trade["expiry_date"], ignoretz=True)

    @property
    def pretty_expiration(self):
        """Generate a pretty expiration date."""
        if not self.is_option_trade:
            return None

        expiration_format = "%-m/%d" if self.dte <= 365 else "%-m/%d/%y"
        return self.parse_expiration().strftime(expiration_format)

    @property
    def pretty_premium(self):
        """Return the price filled in a nice currency format."""
        return "${:,.2f}".format(self.trade["price_filled"])

    @property
    def quantity(self):
        """Extract quantity from the trade."""
        return self.trade["quantity"]

    @property
    def sentiment(self):
        """Determine if trade is bearish, bullish, or neutral."""
        return self.trade_spec["sentiment"]

    @property
    def guid(self):
        """Get the GUID of the trade."""
        return self.trade["guid"]

    @property
    def raw_strikes(self):
        """Get a string containing the strikes from the trade in a generic way."""
        if not self.is_option_trade:
            return None

        strikes = {
            "long put": self.trade["long_put"],
            "short put": self.trade["short_put"],
            "short call": self.trade["short_call"],
            "long call": self.trade["long_call"],
        }
        # Make a string from the generic list of strikes.
        return "/".join([f"${v}" for k, v in strikes.items() if v is not None])

    def save(self):
        """Add the trending ticker to the list of seen trending tickers."""
        self.db["trades"] = set(list(self.db["trades"]) + [self.guid])

    @property
    def short_return(self):
        """Get the return percentage for a short option."""
        match self.trade_type:
            case "CASH SECURED PUT":
                strike = self.trade["short_put"]
            case "COVERED CALL" | "SHORT NAKED CALL":
                strike = self.trade["short_call"]
            case _:
                return None

        premium = self.trade["price_filled"]
        return round((premium / (float(strike) - premium)) * 100, 2)

    @property
    def short_return_annualized(self):
        """Get the annualized return on a short option."""
        # Avoid 0 DTE situations.
        if not self.is_single_option or self.dte < 1:
            return None

        return round((self.short_return / self.dte) * 365, 2)

    @property
    def strike(self):
        """Get the strike for a single option trade."""
        if not self.is_single_option:
            return None

        return self.trade[self.trade_spec["strikes"][0]]

    @property
    def symbol(self):
        """Get the symbol involved in the trade."""
        return self.trade["symbol"]

    @property
    def symbol_chart(self):
        """Get the chart for the stock symbol."""
        return utils.get_stock_chart(self.symbol)

    @property
    def symbol_logo(self):
        """Get the logo for the stock symbol."""
        return utils.get_stock_logo(self.symbol)

    @cached_property
    def trade_spec(self):
        """Return the spec for this trade."""
        specFile = "thetagang_notifications/assets/trade_specs.yml"
        with open(specFile, "r", encoding="utf-8") as fileh:
            return [x for x in yaml.safe_load(fileh) if x["type"] == self.trade_type][0]

    @property
    def trade_type(self):
        """Return the type of trade."""
        return self.trade["type"]

    @property
    def trade_url(self):
        """Generate a URL to the trade itself."""
        return f"https://thetagang.com/{self.username}/{self.guid}"

    @property
    def username(self):
        """Get username of the person making the trade."""
        return self.trade["User"]["username"]


def download_trades():
    """Download the current list of trades from thetagang.com."""
    log.info("🚚 Getting current list of trades...")
    resp = requests.get(config.TRADES_JSON_URL)
    trades_json = resp.json()
    return trades_json["data"]["trades"]


def main():
    """Handle updates for trades."""
    downloaded_trades = download_trades()
    for downloaded_trade in downloaded_trades:
        trade_obj = Trade(downloaded_trade)
        trade_obj.notify()

    return downloaded_trades


if __name__ == "__main__":  # pragma: no cover
    main()
