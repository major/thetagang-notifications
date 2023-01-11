"""Test the trade math functions."""
from thetagang_notifications import trade_math


def test_breakeven_cash_secured_put():
    """Verify breakeven on a CSP."""
    trade = {"type": "CASH SECURED PUT", "short_put": "100", "price_filled": 1.00}
    breakeven = trade_math.breakeven(trade)
    assert breakeven == "99.00"


def test_breakeven_covered_call():
    """Verify breakeven on a covered call."""
    trade = {"type": "COVERED CALL", "short_call": "100", "price_filled": 1.00}
    breakeven = trade_math.breakeven(trade)
    assert breakeven == "101.00"


def test_breakeven_other():
    """Ensure the breakeven function handles other trades."""
    trade = {"type": "SHORT IRON CONDOR"}
    assert trade_math.breakeven(trade) is None
