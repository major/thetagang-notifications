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
    "real_trades",
    ["COVERED CALL", "LONG NAKED CALL", "SHORT NAKED CALL"],
    indirect=True,
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
def test_break_even_not_implemented(real_trades):
    """Test call break even."""
    trade_obj = trade.get_handler(real_trades)
    with pytest.raises(NotImplementedError):
        trade_obj.break_even()


@pytest.mark.parametrize(
    "real_trades",
    ["CASH SECURED PUT", "COVERED CALL", "SHORT NAKED CALL"],
    indirect=True,
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


def test_pretty_expiration(real_trades):
    """Test pretty expiration date formatting."""
    trade_obj = trade.get_handler(real_trades)
    with mock.patch(
        "thetagang_notifications.trade_math.pretty_expiration"
    ) as mock_pretty_expiration:
        if "COMMON STOCK" in trade_obj.trade_type:
            with pytest.raises(NotImplementedError):
                trade_obj.pretty_expiration()
        else:
            trade_obj.pretty_expiration()
            mock_pretty_expiration.assert_called_once()


def test_notification_details(real_trades):
    """Test notification details."""
    trade_obj = trade.get_handler(real_trades)
    result = trade_obj.notification_details()
    # TODO: Improve this test and verify the output of the dict.
    assert isinstance(result, dict)


@pytest.mark.parametrize("real_trades", ["BUY COMMON STOCK"], indirect=True)
def test_annualized_return_not_implemented(real_trades):
    """Test annualized return for a trade that is not implemented."""
    trade_obj = trade.get_handler(real_trades)
    with pytest.raises(NotImplementedError):
        trade_obj.annualized_return()


def test_notification_action(real_trades):
    """Test notification action."""
    trade_obj = trade.get_handler(real_trades)
    result = trade_obj.notification_action()

    assert isinstance(result, dict)
    assert "author" in result
    assert "icon" in result
    assert "url" in result
