"""Parse trades and send notifications."""

from abc import ABC

import yaml

from thetagang_notifications.config import TRADE_SPEC_FILE
from thetagang_notifications.trade_math import short_put_breakeven


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
        self.raw_trade = trade
        self.trade_type = trade["type"]

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
        return NotImplementedError


class CashSecuredPut(Trade):
    """Cash secured put trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_put = self.raw_trade["short_put"]
        self.price_filled = self.raw_trade["price_filled"]

    def break_even(self):
        return short_put_breakeven(self.short_put, self.price_filled)


class CoveredCall(Trade):
    """Covered call trade."""

    def __init__(self, trade):
        """Initialize the trade."""
        super().__init__(trade)
        self.short_call = self.raw_trade["short_call"]
        self.price_filled = self.raw_trade["price_filled"]

    def break_even(self):
        return short_put_breakeven(self.short_call, self.price_filled)


def get_handler(trade):
    """Create a trade object."""
    class_name = convert_to_class_name(trade["type"])
    return globals()[class_name](trade)
