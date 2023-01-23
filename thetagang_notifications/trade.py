"""Parse trades and send notifications."""
import logging

import inflect
import yaml

from thetagang_notifications.config import TRADE_SPEC_FILE
from thetagang_notifications.notification import get_handler as get_notification_handler
from thetagang_notifications.trade_math import (
    call_break_even,
    days_to_expiration,
    pretty_expiration,
    pretty_premium,
    pretty_strike,
    put_break_even,
    short_annualized_return,
    short_option_potential_return,
)

log = logging.getLogger(__name__)


def convert_to_class_name(trade_type):
    """Convert a trade type to a class name."""
    return "".join([word.capitalize() for word in trade_type.split(" ")])


def get_spec_data(trade_type):
    """Get the spec data for a trade type."""
    with open(TRADE_SPEC_FILE, encoding="utf-8") as file_handle:
        spec_data = yaml.safe_load(file_handle)
    return [x for x in spec_data if x["type"] == trade_type][0]


class Trade:
    """Abstract base class for a trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        # Create some class properties from the raw trade data.
        self.expiry_date = trade["expiry_date"]
        self.guid = trade["guid"]
        self.price_filled = trade["price_filled"]
        self.profit = abs(trade["pl"])
        self.quantity = trade["quantity"]
        self.strike = None
        self.symbol = trade["symbol"]
        self.trade_type = trade["type"]
        self.username = trade["User"]["username"]

        # Load properties from the trade_spec file.
        self.is_option_trade = None
        self.is_stock_trade = None
        self.is_single_leg = None
        self.is_multi_leg = None
        self.is_short = None
        self.is_long = None
        self.load_trade_properties()

        # Handle trade status items.
        self.is_open = not trade["close_date"]
        self.is_closed = not self.is_open
        self.is_assigned = trade.get("assigned", False)
        self.is_winner = trade.get("win", False)
        self.is_loser = not self.is_winner
        self.status = "opened" if self.is_open else "closed"

        # Get notes for the trade.
        self.note = trade["note"]
        self.closing_note = trade["closing_note"]

        # Generate common notification elements.
        self.notification_title = f"${self.symbol}: {self.trade_type}"
        self.notification_title += f" ({self.quantity})" if self.quantity > 1 else ""
        self.notification_description = None

        # Log that we're parsing this trade.
        log.info("Processing trade: %s", self.guid)

    def load_trade_properties(self):
        """Load properties from the spec."""
        spec_data = get_spec_data(self.trade_type)

        # Set properties based on date from the trade_spec YAML file.
        self.is_option_trade = spec_data["option_trade"]
        self.is_stock_trade = not spec_data["option_trade"]
        self.is_single_leg = self.is_option_trade and ["single_leg"]
        self.is_multi_leg = self.is_option_trade and not spec_data["single_leg"]
        self.is_short = spec_data["short"]
        self.is_long = not spec_data["short"]

    def annualized_return(self):
        """Return the annualized return for a trade."""
        raise NotImplementedError("Annualized return not implemented for this trade.")

    def break_even(self):
        raise NotImplementedError("Break even not implemented for this trade.")

    def notification_details(self):  # pragma: no cover
        """Return the notification details.

        These are added as individual embeds in the Discord
        notification.
        """
        raise NotImplementedError(
            "Notification details not implemented for this trade."
        )

    def notify(self):
        """Send a notification for the trade."""
        notification_handler = get_notification_handler(self)
        notification_handler.notify()

    def potential_return(self):
        raise NotImplementedError("Potential return not implemented for this trade.")

    def pretty_expiration(self):
        """Return the pretty expiration date for an option trade."""
        return pretty_expiration(self.expiry_date)


class CashSecuredPut(Trade):
    """Cash secured put trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(trade["short_put"])

    def annualized_return(self):
        """Return the annualized return."""
        dte = days_to_expiration(self.expiry_date)
        return short_annualized_return(self.strike, self.price_filled, dte)

    def break_even(self):
        return put_break_even(self.strike, self.price_filled)

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strike": pretty_strike(self.strike),
            "Premium": pretty_premium(self.price_filled),
            "Break even": self.break_even(),
            "Return": (
                f"Ptl: {self.potential_return()}%\nAnn: {self.annualized_return()}%"
            ),
        }

    def potential_return(self):
        """Return the potential return on a short put."""
        return short_option_potential_return(self.strike, self.price_filled)


class CoveredCall(Trade):
    """Covered call trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(trade["short_call"])

    def annualized_return(self):
        """Return the annualized return."""
        dte = days_to_expiration(self.expiry_date)
        return short_annualized_return(self.strike, self.price_filled, dte)

    def break_even(self):
        return call_break_even(self.strike, self.price_filled)

    def potential_return(self):
        """Return the potential return on a short call."""
        return short_option_potential_return(self.strike, self.price_filled)

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strike": pretty_strike(self.strike),
            "Premium": pretty_premium(self.price_filled),
            "Break even": self.break_even(),
            "Return": (
                f"Ptl: {self.potential_return()}%\nAnn: {self.annualized_return()}%"
            ),
        }


class ShortNakedCall(Trade):
    """Short naked call trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(trade["short_call"])

    def annualized_return(self):
        """Return the annualized return."""
        dte = days_to_expiration(self.expiry_date)
        return short_annualized_return(self.strike, self.price_filled, dte)

    def break_even(self):
        return call_break_even(self.strike, self.price_filled)

    def potential_return(self):
        """Return the potential return on a short call."""
        return short_option_potential_return(self.strike, self.price_filled)

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strike": pretty_strike(self.strike),
            "Premium": pretty_premium(self.price_filled),
            "Break even": self.break_even(),
            "Return": (
                f"Ptl: {self.potential_return()}%\nAnn: {self.annualized_return()}%",
            ),
        }


class LongNakedCall(Trade):
    """Long naked call trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(trade["long_call"])

    def break_even(self):
        return call_break_even(self.strike, self.price_filled)

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strike": pretty_strike(self.strike),
            "Premium": pretty_premium(self.price_filled),
            "Break even": self.break_even(),
        }


class LongNakedPut(Trade):
    """Long naked put trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(trade["long_put"])

    def break_even(self):
        return put_break_even(self.strike, self.price_filled)

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strike": pretty_strike(self.strike),
            "Premium": pretty_premium(self.price_filled),
            "Break even": self.break_even(),
        }


class PutCreditSpread(Trade):
    """Put credit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(trade["short_put"])
        self.long_strike = float(trade["long_put"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"{pretty_strike(self.short_strike)}p"
                f"/{pretty_strike(self.long_strike)}p"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class CallCreditSpread(Trade):
    """Call credit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(trade["short_call"])
        self.long_strike = float(trade["long_call"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"{pretty_strike(self.short_strike)}c"
                f"/{pretty_strike(self.long_strike)}c"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class PutDebitSpread(Trade):
    """Put debit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(trade["short_put"])
        self.long_strike = float(trade["long_put"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"{pretty_strike(self.long_strike)}p"
                f"/{pretty_strike(self.short_strike)}p"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class CallDebitSpread(Trade):
    """Call debit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(trade["short_call"])
        self.long_strike = float(trade["long_call"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"{pretty_strike(self.long_strike)}c"
                f"/{pretty_strike(self.short_strike)}c"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class LongStrangle(Trade):
    """Long strangle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(trade["long_call"])
        self.long_put = float(trade["long_put"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"{pretty_strike(self.long_call)}c" f"/{pretty_strike(self.long_put)}p"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class ShortStrangle(Trade):
    """Short strangle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_call = float(trade["short_call"])
        self.short_put = float(trade["short_put"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"{pretty_strike(self.short_call)}c"
                f"/{pretty_strike(self.short_put)}p"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class LongStraddle(Trade):
    """Long straddle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(trade["long_call"])
        self.long_put = float(trade["long_put"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"{pretty_strike(self.long_call)}c/{pretty_strike(self.long_put)}p"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class ShortStraddle(Trade):
    """Short straddle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_call = float(trade["short_call"])
        self.short_put = float(trade["short_put"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"{pretty_strike(self.short_call)}c/{pretty_strike(self.short_put)}p"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class JadeLizard(Trade):
    """Jade lizard trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(trade["long_call"])
        self.short_call = float(trade["short_call"])
        self.short_put = float(trade["short_put"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"Short: {pretty_strike(self.short_put)}p/"
                f"{pretty_strike(self.short_call)}c\n"
                f"Long: {pretty_strike(self.short_put)}p"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class ShortIronCondor(Trade):
    """Short iron condor trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(trade["long_call"])
        self.long_put = float(trade["long_put"])
        self.short_call = float(trade["short_call"])
        self.short_put = float(trade["short_put"])

    def notification_details(self):
        """Return the notification details."""
        return {
            "Expiration": self.pretty_expiration(),
            "Strikes": (
                f"{pretty_strike(self.long_put)}p/{pretty_strike(self.short_put)}p\n"
                f"{pretty_strike(self.long_call)}c/{pretty_strike(self.short_call)}c"
            ),
            "Premium": pretty_premium(self.price_filled),
        }


class BuyCommonStock(Trade):
    """Buy common stock trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        # Common stock trades always use "note" for the trade note.
        self.trade_note = trade["note"]

        # Force stock trades to always show as open.
        self.status = "opened"
        self.is_closed = False
        self.is_open = True

        p = inflect.engine()
        self.notification_title = (
            f"Bought {self.quantity}"
            f" {p.plural('share', self.quantity)} of {self.symbol} "
            f"@ {pretty_strike(self.price_filled)}"
        )

    def pretty_expiration(self):
        raise NotImplementedError

    def notification_details(self):
        """Return the notification details."""
        return {}


class SellCommonStock(Trade):
    """Sell common stock trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        # Common stock trades always use "note" for the trade note.
        self.trade_note = trade["note"]

        # Force stock trades to always show as open.
        self.status = "opened"
        self.is_closed = False
        self.is_open = True

        p = inflect.engine()
        self.notification_title = (
            f"Sold {self.quantity} {p.plural('share', self.quantity)} of {self.symbol} "
            f"@ {pretty_strike(self.price_filled)}"
        )

    def pretty_expiration(self):
        raise NotImplementedError

    def notification_details(self):
        """Return the notification details."""
        return {}


def get_handler(trade):
    """Create a trade object."""
    class_name = convert_to_class_name(trade["type"])
    return globals()[class_name](trade)
