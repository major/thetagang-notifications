"""Pydantic models for trade data validation and type safety."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field, field_validator


class UserData(BaseModel):
    """User information from trade data."""
    username: str
    pfp: Optional[str] = None
    role: str


class TradeData(BaseModel):
    """Validated trade data from API."""
    expiry_date: Optional[str] = None
    guid: str
    price_filled: float
    price_closed: Optional[float] = None
    quantity: int
    symbol: str
    type: str = Field(alias="type")
    user: UserData = Field(alias="User")
    profit_loss_raw: Optional[float] = Field(alias="profitLoss")
    close_date: Optional[datetime] = None
    assigned: bool = False
    win: bool = False
    note: str = ""
    closing_note: str = ""
    mistake: Optional[bool] = None
    
    # Strike prices - these will be populated dynamically based on trade type
    # API sends empty strings for unused strikes, so we need custom validation
    short_put: Optional[float] = None
    long_put: Optional[float] = None
    short_call: Optional[float] = None
    long_call: Optional[float] = None
    long_call2: Optional[float] = None
    
    # Field validators to handle empty strings from API
    @field_validator('short_put', 'long_put', 'short_call', 'long_call', 'long_call2', mode='before')
    @classmethod
    def validate_strike_fields(cls, v):
        """Convert empty strings to None for strike prices."""
        if v == "" or v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None
    
    @field_validator('assigned', 'win', mode='before') 
    @classmethod
    def validate_boolean_fields(cls, v):
        """Convert null values to False for boolean fields."""
        if v is None:
            return False
        return v
            
    @field_validator('closing_note', 'note', mode='before')
    @classmethod  
    def validate_string_fields(cls, v):
        """Convert null values to empty string."""
        if v is None:
            return ""
        return v
    
    @computed_field
    @property
    def is_open(self) -> bool:
        """Check if trade is open."""
        return self.close_date is None
    
    @computed_field  
    @property
    def is_closed(self) -> bool:
        """Check if trade is closed."""
        return not self.is_open
    
    @computed_field
    @property
    def status(self) -> str:
        """Get trade status."""
        return "opened" if self.is_open else "closed"
    
    @computed_field
    @property
    def result(self) -> str:
        """Get trade result."""
        if self.assigned:
            return "Assigned"
        return "Won" if self.win else "Lost"


class TradeSpec(BaseModel):
    """Trade specification from YAML configuration."""
    type: str
    option_trade: bool
    single_leg: bool
    strikes: list[str]
    short: bool
    sentiment: str
    example_guid: str
    
    @computed_field
    @property
    def is_stock_trade(self) -> bool:
        """Check if this is a stock trade."""
        return not self.option_trade
    
    @computed_field
    @property
    def is_multi_leg(self) -> bool:
        """Check if this is a multi-leg option trade."""
        return self.option_trade and not self.single_leg
    
    @computed_field
    @property
    def is_long(self) -> bool:
        """Check if this is a long trade."""
        return not self.short