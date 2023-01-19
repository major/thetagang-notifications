"""Tests for the Trade class and its subclasses."""
from unittest import mock

import pytest

from thetagang_notifications import trade


@pytest.mark.parametrize("real_trades", ["CASH SECURED PUT"], indirect=True)
def test_get_handler(real_trades):
    """Test the Trade class."""
    trade_obj = trade.get_handler(real_trades)
    assert isinstance(trade_obj, trade.CashSecuredPut)


def test_get_handler_unknown_type():
    """Test the Trade class."""
    mock_trade = {"type": "UNKNOWN"}
    with pytest.raises(KeyError):
        trade.get_handler(mock_trade)


@pytest.mark.parametrize(
    "real_trades", ["CASH SECURED PUT", "LONG NAKED PUT"], indirect=True
)
def test_put_break_even(real_trades):
    """Test put break even."""
    with mock.patch(
        "thetagang_notifications.trade_math.put_break_even"
    ) as mock_break_even:
        trade_obj = trade.get_handler(real_trades)
        trade_obj.break_even()
        mock_break_even.assert_called_once()


@pytest.mark.parametrize(
    "real_trades", ["COVERED CALL", "LONG NAKED CALL"], indirect=True
)
def test_call_break_even(real_trades):
    """Test call break even."""
    with mock.patch(
        "thetagang_notifications.trade_math.call_break_even"
    ) as mock_break_even:
        trade_obj = trade.get_handler(real_trades)
        trade_obj.break_even()
        mock_break_even.assert_called_once()


@pytest.mark.parametrize("real_trades", ["PUT CREDIT SPREAD"], indirect=True)
def test_break_even_not_implemeneted(real_trades):
    """Test call break even."""
    trade_obj = trade.get_handler(real_trades)
    with pytest.raises(NotImplementedError):
        trade_obj.break_even()


@pytest.mark.parametrize(
    "real_trades", ["CASH SECURED PUT", "COVERED CALL"], indirect=True
)
def test_potential_return(real_trades):
    """Test potential return."""
    with mock.patch(
        "thetagang_notifications.trade_math.short_option_potential_return"
    ) as mock_potential_return:
        trade_obj = trade.get_handler(real_trades)
        trade_obj.potential_return()
        mock_potential_return.assert_called_once()


@pytest.mark.parametrize("real_trades", ["LONG NAKED CALL"], indirect=True)
def test_potential_return_not_implemented(real_trades):
    """Test a potential return that is not implemented."""
    trade_obj = trade.get_handler(real_trades)
    with pytest.raises(NotImplementedError):
        trade_obj.potential_return()
