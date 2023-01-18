"""Tests for the Trade class and its subclasses."""
import pytest

from thetagang_notifications.trade import CashSecuredPut, get_handler


def test_trade():
    """Test the Trade class."""
    trade = {"trade_type": "CASH SECURED PUT"}
    trade = get_handler(trade)
    assert isinstance(trade, CashSecuredPut)


def test_trade_unknown_type():
    """Test the Trade class."""
    trade = {"trade_type": "UNKNOWN"}
    with pytest.raises(ValueError):
        get_handler(trade)
