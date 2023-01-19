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

        # Load properties from a spec file.
        self.is_option_trade = None
        self.is_stock_trade = None
        self.is_single_leg = None
        self.is_multi_leg = None
        self.is_short = None
        self.is_long = None
        self.load_trade_properties()

    def load_trade_properties(self):
        """Load properties from the spec."""
        spec_data = get_spec_data(self.trade_type)

        # Set properties based on what's in the spec.
        self.is_option_trade = spec_data["option_trade"]
        self.is_stock_trade = not spec_data["option_trade"]
        self.is_single_leg = self.is_option_trade and ["single_leg"]
        self.is_multi_leg = self.is_option_trade and not spec_data["single_leg"]
        self.is_short = spec_data["short"]
        self.is_long = not spec_data["short"]

    def break_even(self):
        raise NotImplementedError("Break even not implemented for this trade.")

    def potential_return(self):
        raise NotImplementedError("Potential return not implemented for this trade.")


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
        self.strike = float(self.raw_trade["short_put"])
        self.long_strike = float(self.raw_trade["long_put"])


def get_handler(trade):
    """Create a trade object."""
    class_name = convert_to_class_name(trade["type"])
    return globals()[class_name](trade)
