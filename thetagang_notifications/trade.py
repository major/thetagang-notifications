"""Parse trades and send notifications."""

import logging

import inflect
import yaml

from thetagang_notifications.config import EMOJI_ASSIGNED, EMOJI_LOSER, EMOJI_WINNER, TRADE_SPEC_FILE
from thetagang_notifications.exceptions import AnnualizedReturnError, BreakEvenError, PotentialReturnError
from thetagang_notifications.notification import get_notifier as get_notification_handler
from thetagang_notifications.trade_math import (
    call_break_even,
    days_to_expiration,
    percentage_profit,
    pretty_expiration,
    pretty_premium,
    pretty_strike,
    put_break_even,
    short_annualized_return,
    short_option_potential_return,
)

log = logging.getLogger(__name__)


def get_spec_data(trade_type):
    """Get the spec data for a trade type."""
    with open(TRADE_SPEC_FILE, encoding="utf-8") as file_handle:
        spec_data = yaml.safe_load(file_handle)
    return next(x for x in spec_data if x["type"] == trade_type)


class Trade:
    """Abstract base class for a trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        # Create some class properties from the raw trade data.
        self.expiry_date = trade["expiry_date"]
        self.guid = trade["guid"]
        self.price_filled = trade["price_filled"]
        self.price_closed = trade["price_closed"]
        self.profit = abs(trade["pl"])
        self.quantity = trade["quantity"]
        self.strike = None
        self.symbol = trade["symbol"]
        self.trade_type = trade["type"]
        self.username = trade["User"]["username"]

        # Load properties from the trade_spec file.
        self.load_trade_properties()

        # Handle trade status items.
        self.is_open = not trade["close_date"]
        self.is_closed = not self.is_open
        self.is_assigned = trade.get("assigned", False)
        self.is_winner = trade.get("win", False)
        self.is_loser = not self.is_winner
        self.status = "opened" if self.is_open else "closed"
        self.result = "Assigned" if self.is_assigned else "Won" if self.is_winner else "Lost"
        self.trade_emoji = EMOJI_ASSIGNED if self.is_assigned else EMOJI_WINNER if self.is_winner else EMOJI_LOSER

        # Get the percentage profit/loss on the trade.
        if not self.is_open and self.is_option_trade:
            self.percentage_profit = percentage_profit(self.is_winner, self.price_filled, self.price_closed)

        # Get notes for the trade.
        self.note = trade["note"]
        self.closing_note = trade["closing_note"]

        # Log that we're parsing this trade.
        log.info("Processing trade: %s", self.guid)

        # Set up a basic header for notifications.
        self.notification_header = f"{self.symbol}: {self.trade_type}"

    def load_trade_properties(self):
        """Load properties from the spec."""
        spec_data = get_spec_data(self.trade_type)

        # Set properties based on date from the trade_spec YAML file.
        self.is_option_trade = spec_data["option_trade"]
        self.is_stock_trade = not spec_data["option_trade"]
        self.is_single_leg = self.is_option_trade and spec_data["single_leg"]
        self.is_multi_leg = self.is_option_trade and not spec_data["single_leg"]
        self.is_short = spec_data["short"]
        self.is_long = not spec_data["short"]

    def annualized_return(self):
        """Return the annualized return for a trade."""
        raise AnnualizedReturnError(self.trade_type)

    def break_even(self):
        raise BreakEvenError(self.trade_type)

    def opening_description(self):
        """Return the notification description for opening trades."""
        desc = f"Break even: {self.break_even()}\n"
        desc += f"Return: {self.potential_return()}% ({self.annualized_return()}% ann.)"
        return desc

    def closing_description(self):
        """Return the notification description for closing trades."""
        if self.is_stock_trade or self.is_open:
            return None

        desc = f"{self.trade_emoji} {self.result} ({self.percentage_profit}%) "
        desc += "" if self.is_assigned else f"{pretty_strike(self.profit * 100)}"
        return desc

    def notification_title(self):
        """Return the notification title."""
        strike_type = "c" if "CALL" in self.trade_type else "p"
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.strike)}{strike_type} "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title

    def notify(self):
        """Send a notification for the trade."""
        notification_handler = get_notification_handler(self)
        notification_handler.notify()

    def potential_return(self):
        raise PotentialReturnError(self.trade_type)

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


class LongNakedCall(Trade):
    """Long naked call trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(trade["long_call"])

    def break_even(self):
        return call_break_even(self.strike, self.price_filled)

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None


class LongNakedPut(Trade):
    """Long naked put trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(trade["long_put"])

    def break_even(self):
        return put_break_even(self.strike, self.price_filled)

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None


class PutCreditSpread(Trade):
    """Put credit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(trade["short_put"])
        self.long_strike = float(trade["long_put"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.short_strike)}p/{pretty_strike(self.long_strike)}p "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


class CallCreditSpread(Trade):
    """Call credit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(trade["short_call"])
        self.long_strike = float(trade["long_call"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.short_strike)}c/{pretty_strike(self.long_strike)}c "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


class PutDebitSpread(Trade):
    """Put debit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(trade["short_put"])
        self.long_strike = float(trade["long_put"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.long_strike)}p/{pretty_strike(self.short_strike)}p "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


class CallDebitSpread(Trade):
    """Call debit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(trade["short_call"])
        self.long_strike = float(trade["long_call"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.long_strike)}c/{pretty_strike(self.short_strike)}c "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


class LongStrangle(Trade):
    """Long strangle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(trade["long_call"])
        self.long_put = float(trade["long_put"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.long_call)}c/{pretty_strike(self.long_put)}p "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


class ShortStrangle(Trade):
    """Short strangle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_call = float(trade["short_call"])
        self.short_put = float(trade["short_put"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.short_call)}c/{pretty_strike(self.short_put)}p "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


class LongStraddle(Trade):
    """Long straddle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(trade["long_call"])
        self.long_put = float(trade["long_put"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.long_call)}c/{pretty_strike(self.long_put)}p "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


class ShortStraddle(Trade):
    """Short straddle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_call = float(trade["short_call"])
        self.short_put = float(trade["short_put"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.short_call)}c/{pretty_strike(self.short_put)}p "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


class JadeLizard(Trade):
    """Jade lizard trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(trade["long_call"])
        self.short_call = float(trade["short_call"])
        self.short_put = float(trade["short_put"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.long_call)}c/{pretty_strike(self.short_call)}c/"
            f"{pretty_strike(self.short_put)}p "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


class ShortIronCondor(Trade):
    """Short iron condor trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(trade["long_call"])
        self.long_put = float(trade["long_put"])
        self.short_call = float(trade["short_call"])
        self.short_put = float(trade["short_put"])

    def opening_description(self):
        """Return the notification description for opening trades."""
        return None

    def notification_title(self):
        """Return the notification title."""
        title = (
            f"{self.quantity} x {pretty_expiration(self.expiry_date)} "
            f"{pretty_strike(self.long_put)}p/{pretty_strike(self.short_put)}p/"
            f"{pretty_strike(self.long_call)}c/{pretty_strike(self.short_call)}c "
            f"for {pretty_premium(self.price_filled)}"
        )
        return self.notification_header + "\n" + title


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

    def pretty_expiration(self):
        raise NotImplementedError

    def closing_description(self):
        return None

    def notification_title(self):
        p = inflect.engine()
        return (
            f"Bought {self.quantity}"
            f" {p.plural('share', self.quantity)} of {self.symbol} "
            f"@ {pretty_strike(self.price_filled)}"
        )

    def opening_description(self):
        return None


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

    def pretty_expiration(self):
        raise NotImplementedError

    def closing_description(self):
        return None

    def notification_title(self):
        p = inflect.engine()
        return (
            f"Sold {self.quantity} {p.plural('share', self.quantity)} of {self.symbol} "
            f"@ {pretty_strike(self.price_filled)}"
        )

    def opening_description(self):
        return None


def get_trade_class(trade):
    """Create a trade object."""
    trade_types = {
        "CASH SECURED PUT": CashSecuredPut,
        "COVERED CALL": CoveredCall,
        "SHORT NAKED CALL": ShortNakedCall,
        "LONG CALL": LongNakedCall,
        "LONG PUT": LongNakedPut,
        "PUT CREDIT SPREAD": PutCreditSpread,
        "CALL CREDIT SPREAD": CallCreditSpread,
        "PUT DEBIT SPREAD": PutDebitSpread,
        "CALL DEBIT SPREAD": CallDebitSpread,
        "LONG STRANGLE": LongStrangle,
        "SHORT STRANGLE": ShortStrangle,
        "LONG STRADDLE": LongStraddle,
        "SHORT STRADDLE": ShortStraddle,
        "JADE LIZARD": JadeLizard,
        "SHORT IRON CONDOR": ShortIronCondor,
        "BUY COMMON STOCK": BuyCommonStock,
        "SELL COMMON STOCK": SellCommonStock,
    }
    return trade_types[trade["type"]](trade)
