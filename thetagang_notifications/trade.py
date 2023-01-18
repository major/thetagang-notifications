"""Parse trades and send notifications."""

from abc import ABC

import yaml

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
        self.raw_trade = trade
        self.trade_type = trade["trade_type"]

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


class CashSecuredPut(Trade):
    """Cash secured put trade."""

    @property
    def friendly_name(self):
        return self.raw_trade


class CoveredCall(Trade):
    """Covered call trade."""

    @property
    def friendly_name(self):
        return self.raw_trade


def get_handler(trade):
    """Create a trade object."""
    class_name = convert_to_class_name(trade["trade_type"])
    try:
        return globals()[class_name](trade)
    except KeyError:
        raise ValueError(f"Unknown trade type: {trade['trade_type']}")
