"""Test the trade math functions."""
from thetagang_notifications import trade_math


def test_break_even_cash_secured_put():
    """Verify breakeven on a CSP."""
    trade = {"type": "CASH SECURED PUT", "short_put": "100", "price_filled": 1.00}
    breakeven = trade_math.breakeven(trade)
    assert breakeven == "99.00"


def test_break_even_covered_call():
    """Verify breakeven on a covered call."""
    trade = {"type": "COVERED CALL", "short_call": "100", "price_filled": 1.00}
    breakeven = trade_math.breakeven(trade)
    assert breakeven == "101.00"


def test_break_even_other():
    """Ensure the break even function handles other trades."""
    trade = {"type": "SHORT IRON CONDOR"}
    assert trade_math.breakeven(trade) is None


def test_short_call_break_even():
    """Verify the break even on a short call."""
    break_even = trade_math.call_break_even(100.00, 1.00)
    assert break_even == 101.00


def tests_short_put_breakeven():
    """Verify the break even on a short put."""
    break_even = trade_math.put_break_even(100.00, 1.00)
    assert break_even == 99.00
