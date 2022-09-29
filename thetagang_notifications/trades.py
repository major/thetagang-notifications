"""Handle trades on thetagang.com."""
from functools import cached_property
from datetime import datetime
import logging
import os
import sys
import yaml

from dateutil import parser
from discord_webhook import DiscordWebhook, DiscordEmbed
from tinydb import TinyDB, Query

from thetagang_notifications import config, thetaget, utils


log = logging.getLogger(__name__)

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
        title = self.get_discord_title_header()
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
            f"[TG: {self.symbol}]"
            f"(https://thetagang.com/symbols/{self.symbol}) | "
            f"[Finviz](https://finviz.com/quote.ashx?t={self.symbol})"
        )

        # Just show links if this is not a short single leg option.
        if not self.is_single_option or not self.is_short:
            return links

        if self.is_open:
            return self.discord_stats_single_leg + links

        return self.discord_stats_single_leg_results + links

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

    @property
    def discord_stats_single_leg_results(self):
        """Generate a report after a trade was closed."""
        profit = "${:,.2f}".format(abs(self.trade['pl'] * 100))

        # Check for assignment.
        if self.is_assigned:
            return f"🚚 ASSIGNED (premium collected: {profit})\n"

        # Check for a winner that wasn't assigned.
        if self.is_winner:
            return f"🟢 WIN: +{profit}\n"

        # Anything left was a loss. 😢
        return f"🔴 LOSS: ({profit})\n"

    def get_discord_title_header(self):
        """Generate the first line of the Discord title."""
        emoji = "🚀 " if self.is_open else "🏁 "

        # Stock purchases are a special case since they're ALWAYS closed.
        if "COMMON STOCK" in self.trade_type:
            emoji = ""

        title = f"{emoji}{self.symbol}: {self.trade_type}\n"
        return title

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
        # Add one extra day to ensure our current day is included in the total.
        # This avoids dividing by zero and also ensures that we calculate DTE
        # just as thetagang.com does. 😉
        return (self.parse_expiration() - datetime.now()).days + 1

    def initialize_db(self):
        """Ensure the database is initialized."""
        dbconn = TinyDB(config.MAIN_TINYDB)
        self.db = dbconn.table('trades')

    @property
    def is_assigned(self):
        """Determine if a closed trade had stock assignment."""
        return self.trade.get('assigned', False)

    @property
    def is_new(self):
        """Determine if the trade is new."""
        Trade = Query()
        return not self.db.contains(Trade.guid == self.guid)

    @property
    def is_open(self):
        """Determine if the trade is open."""
        return True if not self.trade['close_date'] else False

    @property
    def is_recently_closed(self):
        """Determine if the trade is closed."""
        Trade = Query()
        old_trade = self.db.get(Trade.guid == self.guid)
        if not old_trade['close_date'] and self.trade['close_date']:
            return True

        return False

    @property
    def is_option_trade(self):
        """Determine if the trade is an options trade."""
        return self.trade_spec["option_trade"]

    @property
    def is_short(self):
        """Determine if the options trade is short or long."""
        return self.trade_spec["short"]

    @property
    def is_single_option(self):
        """Determine if the trade is a single option trade."""
        return self.trade_spec["single_option"]

    @property
    def is_winner(self):
        """Determine if a closed trade is a winner."""
        return self.trade['win']

    def notify(self):
        """Send notification to Discord."""

        if os.environ.get("PRIME_DATABASE", None) == "yes":
            log.info("Priming database with trade %s", self.guid)
            self.save()
            return None

        # Skip old trades that are still open.
        if not self.is_new and not self.is_recently_closed:
            log.info("👀 Old trade still open: %s", self.trade_url)
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

        embed.set_thumbnail(url=self.symbol_logo)

        # Assume a closing note by default.
        trade_notes = self.trade['closing_note']

        # Use the original opening note if the trade is open or if it's a
        # common stock trade since stock trades have opening notes only.
        if "COMMON STOCK" in self.trade_type or self.is_open:
            trade_notes = self.trade['note']

        # Only add a footer if the user added a note.
        if trade_notes:
            embed.set_footer(text=f"{self.username}: {trade_notes}")

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
        """Get a string containing the strikes from the trade."""
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
        Trade = Query()
        self.db.upsert(self.trade, Trade.guid == self.guid)

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


def check_for_empty_db():
    """Check for an empty database to avoid blasting Discord."""
    trade_obj = Trade({'test': 'test'})

    # Count rows in the database.
    trades_in_db = len(trade_obj.db.all())

    # Stop now if the database is empty and PRIME_DATABASE is not set.
    if trades_in_db < 1 and os.environ.get("PRIME_DATABASE", None) != "yes":
        log.error("Database is empty and PRIME_DATABASE is not set")
        sys.exit()


def main():
    """Handle updates for trades."""
    check_for_empty_db()

    downloaded_trades = thetaget.get_patron_trades()
    for downloaded_trade in downloaded_trades:
        trade_obj = Trade(downloaded_trade)
        trade_obj.notify()

    return downloaded_trades


if __name__ == "__main__":  # pragma: no cover
    main()
