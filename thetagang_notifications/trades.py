"""Handle trades on thetagang.com."""
import logging
from datetime import datetime
from functools import cached_property

import yaml
from dateutil import parser
from discord_webhook import DiscordEmbed, DiscordWebhook

from thetagang_notifications import config, trade_math, trade_queue, utils

log = logging.getLogger(__name__)


class Trade:
    """Class for handling new trades opened on thetagang.com."""

    def __init__(self, trade):
        """Initialize the basics of the class."""
        self.trade = trade

    @property
    def discord_title(self):
        """Generate a title for discord messages."""
        title = self.get_discord_title_header()
        if self.is_option_trade and self.is_single_leg:
            # We have a long/short single leg trade.
            title += self.get_discord_title_single_leg()
        elif self.is_option_trade and not self.is_single_leg:
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

        # Show the results of a closed *option* trade.
        if not self.is_open and self.is_option_trade:
            return self.discord_stats_single_leg_results + links

        # Just show links if this is not a short single leg option.
        if not self.is_single_leg or not self.is_short:
            return links

        if self.is_open:
            return self.discord_stats_single_leg + links

        return links

    @property
    def discord_stats_single_leg(self):
        """Generate stats for a single leg option."""
        # Only support single leg *short* options right now.
        if self.is_single_leg and self.is_short:
            breakeven = trade_math.breakeven(self.trade)
            return (
                f"${breakeven} breakeven\n"
                f"{self.short_return}% potential return "
                f"({self.short_return_annualized}% annualized)\n"
            )

        return ""

    @property
    def discord_stats_single_leg_results(self):
        """Generate a report after a trade was closed."""
        profit_value = abs(self.trade["pl"] * 100)
        profit = f"${profit_value:.2f}"

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
        if not self.is_option_trade:
            emoji = ""

        return f"{emoji}{self.symbol}: {self.trade_type}\n"

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

    @property
    def is_assigned(self):
        """Determine if a closed trade had stock assignment."""
        return self.trade.get("assigned", False)

    @property
    def is_open(self):
        """Determine if the trade is open."""
        # NOTE(mhayden): Stock trades are ALWAYS closed immediately.
        return not self.trade["close_date"]

    @property
    def is_option_trade(self):
        """Determine if the trade is an options trade."""
        return self.trade_spec["option_trade"]

    @property
    def is_short(self):
        """Determine if the options trade is short or long."""
        return self.trade_spec["short"]

    @property
    def is_single_leg(self):
        """Determine if the trade is a single option trade."""
        return self.trade_spec["single_option"]

    @property
    def is_winner(self):
        """Determine if a closed trade is a winner."""
        return self.trade["win"]

    def notify(self):
        """Send notification to Discord."""
        webhook = DiscordWebhook(
            url=config.WEBHOOK_URL_TRADES,
            rate_limit_retry=True,
            username=config.DISCORD_USERNAME,
        )
        webhook.add_embed(self.prepare_embed())
        webhook.execute()

        return webhook

    def prepare_embed(self):
        """Prepare the webhook embed data."""
        embed = DiscordEmbed(
            title=self.discord_title,
            description=self.discord_description,
        )

        # Add thin and wide transparent png to keep the same width for all of
        # the notifications.
        embed.set_image(url="https://major.io/transparent.png")

        embed.set_thumbnail(url=self.symbol_logo)

        # Assume a closing note by default.
        trade_notes = self.trade["closing_note"]

        # Use the original opening note if the trade is open or if it's a
        # common stock trade since stock trades have opening notes only.
        if not self.is_option_trade or self.is_open:
            trade_notes = self.trade["note"]

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
        return f"${self.trade['price_filled']:.2f}"

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
        if not self.is_single_leg or self.dte < 1:
            return None

        return round((self.short_return / self.dte) * 365, 2)

    @property
    def status(self):
        """Determine if the trade is open or closed."""
        return "open" if self.is_open else "closed"

    @property
    def strike(self):
        """Get the strike for a single option trade."""
        if not self.is_single_leg:
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
        spec_file = "thetagang_notifications/assets/trade_specs.yml"
        with open(spec_file, encoding="utf-8") as fileh:
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


def main():
    """Handle updates for trades."""
    for queued_trade in trade_queue.build_queue():
        trade_obj = Trade(queued_trade)
        trade_obj.notify()


if __name__ == "__main__":  # pragma: no cover
    main()
