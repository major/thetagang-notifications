"""Tests for the Trade class and its subclasses."""
import pytest

from thetagang_notifications import trade


@pytest.mark.parametrize("real_trades", ["CASH SECURED PUT"], indirect=True)
def test_trade(real_trades):
    """Test the Trade class."""
    trade_obj = trade.get_handler(real_trades)

    assert isinstance(trade_obj, trade.CashSecuredPut)


def test_trade_unknown_type():
    """Test the Trade class."""
    mock_trade = {"type": "UNKNOWN"}
    with pytest.raises(KeyError):
        trade.get_handler(mock_trade)
