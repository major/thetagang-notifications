"""Parse trades and send notifications."""

from abc import ABC

import yaml

from thetagang_notifications import trade_math
from thetagang_notifications.config import TRADE_SPEC_FILE


def convert_to_class_name(trade_type):
    """Convert a trade type to a class name."""
    return "".join([word.capitalize() for word in trade_type.split(" ")])


def get_spec_data(trade_type):
    """Get the spec data for a trade type."""
    with open(TRADE_SPEC_FILE, encoding="utf-8") as file_handle:
        spec_data = yaml.safe_load(file_handle)
    return [x for x in spec_data if x["type"] == trade_type][0]


class Trade(ABC):
    """Abstract base class for a trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        # Create some class properties from the raw trade data.
        self.raw_trade = trade
        self.trade_type = trade["type"]
        self.symbol = trade["symbol"]
        self.price_filled = trade["price_filled"]
        self.expiry_date = trade["expiry_date"]
        self.quantity = trade["quantity"]

        # Load properties from a spec file.
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
        self.is_winner = trade.get("winner", False)
        self.is_loser = not self.is_winner

        # Load the trade note depending on the status.
        self.trade_note = trade["note"] if self.is_open else trade["closing_note"]

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

    def break_even(self):
        raise NotImplementedError("Break even not implemented for this trade.")

    def dte(self):
        """Return the days to expiration."""
        return trade_math.days_to_expiration(self.expiry_date)

    def potential_return(self):
        raise NotImplementedError("Potential return not implemented for this trade.")

    def parse_expiration(self):
        """Return the expiration date for a short put."""
        return trade_math.parse_expiration(self.expiry_date)


class CashSecuredPut(Trade):
    """Cash secured put trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(self.raw_trade["short_put"])

    def break_even(self):
        return trade_math.put_break_even(self.strike, self.price_filled)

    def potential_return(self):
        """Return the potential return on a short put."""
        return trade_math.short_option_potential_return(self.strike, self.price_filled)


class CoveredCall(Trade):
    """Covered call trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(self.raw_trade["short_call"])

    def break_even(self):
        return trade_math.call_break_even(self.strike, self.price_filled)

    def potential_return(self):
        """Return the potential return on a short call."""
        return trade_math.short_option_potential_return(self.strike, self.price_filled)


class ShortNakedCall(Trade):
    """Short naked call trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(self.raw_trade["short_call"])

    def break_even(self):
        return trade_math.call_break_even(self.strike, self.price_filled)

    def potential_return(self):
        """Return the potential return on a short call."""
        return trade_math.short_option_potential_return(self.strike, self.price_filled)


class LongNakedCall(Trade):
    """Long naked call trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(self.raw_trade["long_call"])

    def break_even(self):
        return trade_math.call_break_even(self.strike, self.price_filled)


class LongNakedPut(Trade):
    """Long naked put trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.strike = float(self.raw_trade["long_put"])

    def break_even(self):
        return trade_math.put_break_even(self.strike, self.price_filled)


class PutCreditSpread(Trade):
    """Put credit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(self.raw_trade["short_put"])
        self.long_strike = float(self.raw_trade["long_put"])


class CallCreditSpread(Trade):
    """Call credit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(self.raw_trade["short_call"])
        self.long_strike = float(self.raw_trade["long_call"])


class PutDebitSpread(Trade):
    """Put debit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(self.raw_trade["short_put"])
        self.long_strike = float(self.raw_trade["long_put"])


class CallDebitSpread(Trade):
    """Call debit spread trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_strike = float(self.raw_trade["short_call"])
        self.long_strike = float(self.raw_trade["long_call"])


class LongStrangle(Trade):
    """Long strangle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(self.raw_trade["long_call"])
        self.long_put = float(self.raw_trade["long_put"])


class ShortStrangle(Trade):
    """Short strangle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_call = float(self.raw_trade["short_call"])
        self.short_put = float(self.raw_trade["short_put"])


class LongStraddle(Trade):
    """Long straddle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(self.raw_trade["long_call"])
        self.long_put = float(self.raw_trade["long_put"])


class ShortStraddle(Trade):
    """Short straddle trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_call = float(self.raw_trade["short_call"])
        self.short_put = float(self.raw_trade["short_put"])


class BuyCommonStock(Trade):
    """Buy common stock trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        # Common stock trades always use "note" for the trade note.
        self.trade_note = trade["note"]

    def dte(self):
        raise NotImplementedError

    def parse_expiration(self):
        raise NotImplementedError


class SellCommonStock(Trade):
    """Sell common stock trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        # Common stock trades always use "note" for the trade note.
        self.trade_note = trade["note"]

    def dte(self):
        raise NotImplementedError

    def parse_expiration(self):
        raise NotImplementedError


class JadeLizard(Trade):
    """Jade lizard trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(self.raw_trade["long_call"])
        self.short_call = float(self.raw_trade["short_call"])
        self.short_put = float(self.raw_trade["short_put"])


class ShortIronCondor(Trade):
    """Short iron condor trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.long_call = float(self.raw_trade["long_call"])
        self.long_put = float(self.raw_trade["long_put"])
        self.short_call = float(self.raw_trade["short_call"])
        self.short_put = float(self.raw_trade["short_put"])


def get_handler(trade):
    """Create a trade object."""
    class_name = convert_to_class_name(trade["type"])
    return globals()[class_name](trade)
