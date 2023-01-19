"""Test the trade math functions."""
from freezegun import freeze_time

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


def test_parse_expiration():
    """Verify the expiration date is parsed."""
    expiration = trade_math.parse_expiration("2022-11-04T05:00:00.000Z")
    assert expiration.year == 2022
    assert expiration.month == 11
    assert expiration.day == 4
    assert expiration.hour == 5
    assert expiration.minute == 0
    assert expiration.second == 0


@freeze_time("2023-01-01")
def test_days_to_expiration():
    """Verify the days to expiration is calculated."""
    dte = trade_math.days_to_expiration("2023-01-10T00:00:00.000Z")
    assert dte == 10


def test_short_call_break_even():
    """Verify the break even on a short call."""
    break_even = trade_math.call_break_even(100.00, 1.00)
    assert break_even == 101.00


def test_short_put_break_even():
    """Verify the break even on a short put."""
    break_even = trade_math.put_break_even(100.00, 1.00)
    assert break_even == 99.00


def test_short_option_potential_return():
    """Verify the potential return on a short option."""
    potential_return = trade_math.short_option_potential_return(100.00, 1.00)
    assert potential_return == 1.01


def test_short_annualized_return():
    """Verify the annualized return on a short option."""
    annualized_return = trade_math.short_annualized_return(100.00, 1.00, 30)
    assert annualized_return == 12.29
