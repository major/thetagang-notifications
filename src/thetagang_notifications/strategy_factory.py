"""Factory for creating appropriate strategies based on trade type."""

from typing import TYPE_CHECKING

from thetagang_notifications.strategies import (
    CalculationStrategy,
    ComplexOptionNotificationStrategy,
    DefaultCalculationStrategy,
    NotificationStrategy,
    SingleLegCalculationStrategy,
    SingleLegNotificationStrategy,
    SpreadNotificationStrategy,
    StockNotificationStrategy,
)

if TYPE_CHECKING:
    from thetagang_notifications.models import TradeSpec


class StrategyFactory:
    """Factory for creating appropriate strategies based on trade specifications."""
    
    # Complex options that need special title formatting
    COMPLEX_OPTIONS = {
        "JADE LIZARD",
        "SHORT IRON CONDOR", 
        "SHORT IRON BUTTERFLY",
        "BUTTERFLY CALL DEBIT SPREAD"
    }
    
    @staticmethod
    def create_calculation_strategy(trade_spec: "TradeSpec") -> CalculationStrategy:
        """Create appropriate calculation strategy."""
        if trade_spec.is_stock_trade:
            return DefaultCalculationStrategy()
        elif trade_spec.single_leg:
            return SingleLegCalculationStrategy()
        else:
            # Most multi-leg options don't have break-even calculations implemented yet
            return DefaultCalculationStrategy()
    
    @staticmethod
    def create_notification_strategy(trade_spec: "TradeSpec") -> NotificationStrategy:
        """Create appropriate notification strategy."""
        if trade_spec.is_stock_trade:
            return StockNotificationStrategy()
        elif trade_spec.single_leg:
            return SingleLegNotificationStrategy()
        elif trade_spec.type in StrategyFactory.COMPLEX_OPTIONS:
            return ComplexOptionNotificationStrategy()
        else:
            # Regular spreads and other multi-leg options
            return SpreadNotificationStrategy()