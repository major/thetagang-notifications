"""Parse trades and send notifications."""

import logging

from pydantic import ValidationError
from ruyaml import YAML

from thetagang_notifications.config import settings
from thetagang_notifications.exceptions import AnnualizedReturnError, BreakEvenError, PotentialReturnError
from thetagang_notifications.models import TradeData, TradeSpec
from thetagang_notifications.notification import get_notifier as get_notification_handler
from thetagang_notifications.strategies import StrikeExtractor
from thetagang_notifications.strategy_factory import StrategyFactory
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

# Make exceptions and functions available for backward compatibility
__all__ = [
    "Trade", "ShortSingleLegOption", "LongSingleLegOption", "SpreadOption", 
    "JadeLizard", "ShortIronCondor", "CommonStock", "ButterflyCallDebitSpread", 
    "ShortIronButterfly", "get_trade_class", "get_spec_data",
    "AnnualizedReturnError", "BreakEvenError", "PotentialReturnError",
    "call_break_even", "days_to_expiration", "pretty_expiration", "pretty_premium",
    "pretty_strike", "put_break_even", "short_annualized_return", "short_option_potential_return"
]

# Exceptions are already imported and available for export


def get_spec_data(trade_type: str) -> TradeSpec:
    """Get the spec data for a trade type."""
    yaml = YAML(typ='safe', pure=True)
    with open(settings.trade_spec_file, encoding="utf-8") as file_handle:
        spec_data = yaml.load(file_handle)
    raw_spec = next(x for x in spec_data if x["type"] == trade_type)
    return TradeSpec(**raw_spec)


class Trade:
    """Modern trade class using composition with strategies."""

    def __init__(self, trade: dict):
        """Initialize the trade with pydantic validation and strategies."""
        # Validate and parse trade data
        try:
            self.data = TradeData(**trade)
        except ValidationError as e:
            log.error("Failed to validate trade data: %s", e)
            raise
        
        # Load trade specification
        self.spec = get_spec_data(self.data.type)
        
        # Set up strategies based on trade type
        self.calc_strategy = StrategyFactory.create_calculation_strategy(self.spec)
        self.notification_strategy = StrategyFactory.create_notification_strategy(self.spec)
        
        # Extract strikes based on spec
        self.strikes = StrikeExtractor.extract_strikes(self.data, self.spec)
        
        # Calculate main strike for backward compatibility
        self.strike = StrikeExtractor.get_primary_strike(self.data, self.spec)
        
        # Set up commonly used properties for backward compatibility
        self.expiry_date = self.data.expiry_date
        self.guid = self.data.guid
        self.price_filled = self.data.price_filled
        self.price_closed = self.data.price_closed
        self.quantity = self.data.quantity
        self.symbol = self.data.symbol
        self.trade_type = self.data.type
        self.username = self.data.user.username
        self.avatar = self.data.user.pfp
        self.profit_loss_raw = self.data.profit_loss_raw
        
        # Derived properties
        self.is_option_trade = self.spec.option_trade
        self.is_stock_trade = self.spec.is_stock_trade
        self.is_single_leg = self.spec.single_leg
        self.is_multi_leg = self.spec.is_multi_leg
        self.is_short = self.spec.short
        self.is_long = self.spec.is_long
        
        # Status properties
        self.is_open = self.data.is_open
        self.is_closed = self.data.is_closed
        self.is_assigned = self.data.assigned
        self.is_winner = self.data.win
        self.is_loser = not self.data.win
        self.status = self.data.status
        self.result = self.data.result
        self.trade_emoji = settings.emoji_assigned if self.is_assigned else settings.emoji_winner if self.is_winner else settings.emoji_loser
        
        # Calculate percentage profit for closed option trades
        if not self.is_open and self.is_option_trade and self.price_closed is not None:
            self.percentage_profit = percentage_profit(self.is_winner, self.price_filled, self.price_closed)
        else:
            self.percentage_profit = 0.0
        
        # Notes
        self.note = self.data.note
        self.closing_note = self.data.closing_note
        
        # Notification setup
        self.trade_note = self.note if self.is_open else self.closing_note
        
        log.info("Processing trade: %s", self.guid)

    def annualized_return(self) -> float:
        """Return the annualized return for a trade."""
        return self.calc_strategy.calculate_annualized_return(self.data, self.spec, self.strikes)

    def break_even(self) -> str:
        """Calculate break even using strategy."""
        return self.calc_strategy.calculate_break_even(self.data, self.spec, self.strikes)

    def closing_description(self) -> str:
        """Return the notification description for closing trades."""
        if self.is_stock_trade or self.is_open:
            return ""

        desc = f"{self.trade_emoji} {self.result} "
        if not self.is_assigned and hasattr(self, 'percentage_profit'):
            desc += f"{pretty_strike(self.profit())} ({self.percentage_profit}%)"
        return desc

    def opening_description(self) -> str:
        """Return the notification description for opening trades."""
        try:
            break_even = self.break_even()
        except BreakEvenError:
            break_even = ""
        
        try:
            potential_return = self.potential_return()
        except PotentialReturnError:
            potential_return = 0.0
            
        try:
            annualized_return = self.annualized_return()
        except AnnualizedReturnError:
            annualized_return = 0.0
        
        return self.notification_strategy.format_opening_description(
            self.data, self.spec, self.strikes,
            break_even, potential_return, annualized_return
        )

    def notification_title(self) -> str:
        """Return the notification title."""
        return self.notification_strategy.format_title(self.data, self.spec, self.strikes)

    def notify(self) -> None:
        """Send a notification for the trade."""
        notification_handler = get_notification_handler(self)
        notification_handler.notify()

    def potential_return(self) -> float:
        """Return the potential return using strategy."""
        return self.calc_strategy.calculate_potential_return(self.data, self.spec, self.strikes)

    def profit(self) -> float:
        """Return the profit on a trade."""
        return abs(float(self.profit_loss_raw or 0.0))

    def pretty_expiration(self) -> str:
        """Return the pretty expiration date for an option trade."""
        if self.expiry_date:
            return pretty_expiration(self.expiry_date)
        return ""


class ShortSingleLegOption(Trade):
    """Short single leg option trades - now uses strategy pattern."""
    pass


class LongSingleLegOption(Trade):
    """Long single leg option trades - now uses strategy pattern."""
    pass


class SpreadOption(Trade):
    """Long or short spread option trades - now uses strategy pattern."""
    pass


class JadeLizard(Trade):
    """Jade lizard trade - now uses strategy pattern."""
    pass


class ShortIronCondor(Trade):
    """Short iron condor trade - now uses strategy pattern."""
    pass


class CommonStock(Trade):
    """Buy or sell common stock trade - now uses strategy pattern."""
    
    def __init__(self, trade: dict):
        """Initialize the trade."""
        super().__init__(trade)
        # Force stock trades to always show as open
        self.status = "opened"
        self.is_closed = False
        self.is_open = True

    def pretty_expiration(self) -> str:
        """Stock trades have no expiration date."""
        raise NotImplementedError


class ButterflyCallDebitSpread(Trade):
    """Butterfly call debit spread trade - now uses strategy pattern."""
    pass


class ShortIronButterfly(Trade):
    """Short iron butterfly trade - now uses strategy pattern."""
    pass


def get_trade_class(trade: dict) -> Trade:
    """Create a trade object."""
    trade_types = {
        "CASH SECURED PUT": ShortSingleLegOption,
        "COVERED CALL": ShortSingleLegOption,
        "SHORT NAKED CALL": ShortSingleLegOption,
        "LONG CALL": LongSingleLegOption,
        "LONG PUT": LongSingleLegOption,
        "PUT CREDIT SPREAD": SpreadOption,
        "CALL CREDIT SPREAD": SpreadOption,
        "PUT DEBIT SPREAD": SpreadOption,
        "CALL DEBIT SPREAD": SpreadOption,
        "LONG STRANGLE": SpreadOption,
        "SHORT STRANGLE": SpreadOption,
        "LONG STRADDLE": SpreadOption,
        "SHORT STRADDLE": SpreadOption,
        "JADE LIZARD": JadeLizard,
        "BUTTERFLY CALL DEBIT SPREAD": ButterflyCallDebitSpread,
        "SHORT IRON CONDOR": ShortIronCondor,
        "SHORT IRON BUTTERFLY": ShortIronButterfly,
        "BUY COMMON STOCK": CommonStock,
        "SELL COMMON STOCK": CommonStock,
    }
    return trade_types[trade["type"]](trade)
