"""Strategy classes for different trade behaviors."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import inflect

from thetagang_notifications.exceptions import AnnualizedReturnError, BreakEvenError, PotentialReturnError
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

if TYPE_CHECKING:
    from thetagang_notifications.models import TradeData, TradeSpec


class StrikeExtractor:
    """Utility class for extracting strike prices from trade data."""
    
    @staticmethod
    def extract_strikes(trade_data: "TradeData", trade_spec: "TradeSpec") -> dict[str, float]:
        """Extract strike prices based on trade spec."""
        strikes = {}
        for strike_field in trade_spec.strikes:
            if hasattr(trade_data, strike_field) and getattr(trade_data, strike_field) is not None:
                strikes[strike_field] = float(getattr(trade_data, strike_field))
        return strikes
    
    @staticmethod
    def get_primary_strike(trade_data: "TradeData", trade_spec: "TradeSpec") -> float:
        """Get the primary strike price for single-leg trades."""
        if not trade_spec.strikes:
            return 0.0
        strike_field = trade_spec.strikes[0]
        return float(getattr(trade_data, strike_field, 0.0))


class CalculationStrategy(ABC):
    """Abstract strategy for trade calculations."""
    
    @abstractmethod
    def calculate_break_even(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> str:
        """Calculate break even point."""
        pass
    
    @abstractmethod
    def calculate_potential_return(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> float:
        """Calculate potential return."""
        pass
    
    @abstractmethod
    def calculate_annualized_return(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> float:
        """Calculate annualized return."""
        pass


class SingleLegCalculationStrategy(CalculationStrategy):
    """Calculation strategy for single-leg options."""
    
    def calculate_break_even(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> str:
        """Calculate break even for single leg option."""
        primary_strike = StrikeExtractor.get_primary_strike(trade_data, trade_spec)
        if "PUT" in trade_data.type:
            return put_break_even(primary_strike, trade_data.price_filled)
        else:
            return call_break_even(primary_strike, trade_data.price_filled)
    
    def calculate_potential_return(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> float:
        """Calculate potential return for single leg option."""
        if not trade_spec.short:
            raise PotentialReturnError(f"Potential return not implemented for {trade_data.type}")
        primary_strike = StrikeExtractor.get_primary_strike(trade_data, trade_spec)
        return short_option_potential_return(primary_strike, trade_data.price_filled)
    
    def calculate_annualized_return(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> float:
        """Calculate annualized return for single leg option."""
        if not trade_spec.short or not trade_data.expiry_date:
            raise AnnualizedReturnError(f"Annualized return not implemented for {trade_data.type}")
        primary_strike = StrikeExtractor.get_primary_strike(trade_data, trade_spec)
        dte = days_to_expiration(trade_data.expiry_date)
        return short_annualized_return(primary_strike, trade_data.price_filled, dte)


class DefaultCalculationStrategy(CalculationStrategy):
    """Default calculation strategy for trades without specific calculations."""
    
    def calculate_break_even(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> str:
        """No break even calculation for this trade type."""
        raise BreakEvenError(f"Break even not implemented for {trade_data.type}")
    
    def calculate_potential_return(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> float:
        """No potential return calculation for this trade type."""
        raise PotentialReturnError(f"Potential return not implemented for {trade_data.type}")
    
    def calculate_annualized_return(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> float:
        """No annualized return calculation for this trade type."""
        raise AnnualizedReturnError(f"Annualized return not implemented for {trade_data.type}")


class NotificationStrategy(ABC):
    """Abstract strategy for notification formatting."""
    
    @abstractmethod
    def format_title(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> str:
        """Format notification title."""
        pass
    
    @abstractmethod
    def format_opening_description(
        self, 
        trade_data: "TradeData", 
        trade_spec: "TradeSpec", 
        strikes: dict[str, float],
        break_even: str,
        potential_return: float,
        annualized_return: float
    ) -> str:
        """Format opening description."""
        pass


class SingleLegNotificationStrategy(NotificationStrategy):
    """Notification strategy for single-leg options."""
    
    def format_title(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> str:
        """Format title for single leg option."""
        strike_type = "c" if "CALL" in trade_data.type else "p"
        primary_strike = StrikeExtractor.get_primary_strike(trade_data, trade_spec)
        
        if trade_data.expiry_date:
            title = (
                f"{trade_data.quantity} x {pretty_expiration(trade_data.expiry_date)} "
                f"{pretty_strike(primary_strike)}{strike_type} "
                f"for {pretty_premium(trade_data.price_filled)}"
            )
        else:
            title = f"{trade_data.quantity} x {pretty_strike(primary_strike)}{strike_type} for {pretty_premium(trade_data.price_filled)}"
        
        return f"{trade_data.symbol}: {trade_data.type}\n{title}"
    
    def format_opening_description(
        self, 
        trade_data: "TradeData", 
        trade_spec: "TradeSpec", 
        strikes: dict[str, float],
        break_even: str,
        potential_return: float,
        annualized_return: float
    ) -> str:
        """Format opening description for single leg option."""
        if not trade_spec.short:
            return ""  # Long options don't show break even/return info
        
        desc = f"Break even: {break_even}\n"
        desc += f"Return: {potential_return}% ({annualized_return}% ann.)"
        return desc


class SpreadNotificationStrategy(NotificationStrategy):
    """Notification strategy for spread options."""
    
    def format_title(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> str:
        """Format title for spread option."""
        strike_strings = [str(strikes.get(field, 0)) for field in trade_spec.strikes]
        
        if trade_data.expiry_date:
            title = (
                f"{trade_data.quantity} x {pretty_expiration(trade_data.expiry_date)} "
                f"{'/'.join(strike_strings)} "
                f"for {pretty_premium(trade_data.price_filled)}"
            )
        else:
            title = f"{trade_data.quantity} x {'/'.join(strike_strings)} for {pretty_premium(trade_data.price_filled)}"
            
        return f"{trade_data.symbol}: {trade_data.type}\n{title}"
    
    def format_opening_description(
        self, 
        trade_data: "TradeData", 
        trade_spec: "TradeSpec", 
        strikes: dict[str, float],
        break_even: str,
        potential_return: float,
        annualized_return: float
    ) -> str:
        """Format opening description for spread option."""
        return ""  # Most spreads don't show opening descriptions


class ComplexOptionNotificationStrategy(NotificationStrategy):
    """Notification strategy for complex multi-leg options like Iron Condor, Jade Lizard."""
    
    def format_title(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> str:
        """Format title for complex option."""
        # Build strike string with option types
        strike_parts = []
        for field in trade_spec.strikes:
            strike_value = strikes.get(field, 0)
            option_type = "c" if "call" in field else "p"
            strike_parts.append(f"{pretty_strike(strike_value)}{option_type}")
        
        if trade_data.expiry_date:
            title = (
                f"{trade_data.quantity} x {pretty_expiration(trade_data.expiry_date)} "
                f"{'/'.join(strike_parts)} "
                f"for {pretty_premium(trade_data.price_filled)}"
            )
        else:
            title = f"{trade_data.quantity} x {'/'.join(strike_parts)} for {pretty_premium(trade_data.price_filled)}"
            
        return f"{trade_data.symbol}: {trade_data.type}\n{title}"
    
    def format_opening_description(
        self, 
        trade_data: "TradeData", 
        trade_spec: "TradeSpec", 
        strikes: dict[str, float],
        break_even: str,
        potential_return: float,
        annualized_return: float
    ) -> str:
        """Format opening description for complex option."""
        return ""


class StockNotificationStrategy(NotificationStrategy):
    """Notification strategy for stock trades."""
    
    def format_title(self, trade_data: "TradeData", trade_spec: "TradeSpec", strikes: dict[str, float]) -> str:
        """Format title for stock trade."""
        p = inflect.engine()
        action = "Bought" if "BUY" in trade_data.type else "Sold"
        return (
            f"{action} {trade_data.quantity}"
            f" {p.plural('share', trade_data.quantity)} of {trade_data.symbol} "  # type: ignore[arg-type]
            f"@ {pretty_strike(trade_data.price_filled)}"
        )
    
    def format_opening_description(
        self, 
        trade_data: "TradeData", 
        trade_spec: "TradeSpec", 
        strikes: dict[str, float],
        break_even: str,
        potential_return: float,
        annualized_return: float
    ) -> str:
        """Format opening description for stock trade."""
        return ""