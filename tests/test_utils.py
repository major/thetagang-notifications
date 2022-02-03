"""Tests for utils functions."""
from datetime import datetime


from freezegun import freeze_time
import pytest


from thetagang_notifications import utils


def test_put_breakeven():
    """Verify that we calculate put breakevens correctly."""
    assert utils.get_put_breakeven(100, 1) == 99


def test_call_breakeven():
    """Verify that we calculate call breakevens correctly."""
    assert utils.get_call_breakeven(100, 1) == 101


def test_parse_expiry_date():
    """Verify that JSON timestamps for expiration dates convert correctly."""
    expiry_date = "2022-03-17T00:00:00.000Z"
    parsed_date = datetime(2022, 3, 17)
    assert utils.parse_expiry_date(expiry_date) == parsed_date


def test_parse_expiry_date_missing():
    """Handle trades without an expiration date."""
    expiry_date = None
    assert utils.parse_expiry_date(expiry_date) is None


@freeze_time("2022-02-01")
def test_get_dte():
    """Verify that DTE is calculated correctly."""
    expiration = "2022-03-18T00:00:00.000Z"
    expected_dte = 45
    assert utils.get_dte(expiration) == expected_dte


@freeze_time("2022-02-01")
def test_get_pretty_expiration():
    """Verify that we generate expiration dates properly in a pretty way."""
    # < 1 year away.
    expiry = "2022-03-17T00:00:00.000Z"
    assert utils.get_pretty_expiration(expiry) == "03/17"

    # > 1 year away.
    expiry = "2023-02-02T00:00:00.000Z"
    assert utils.get_pretty_expiration(expiry) == "02/02/23"

    # Looking backwards.
    expiry = "2021-02-02T00:00:00.000Z"
    assert utils.get_pretty_expiration(expiry) == "02/02"


def test_get_stock_chart():
    """Ensure we can get a chart URL."""
    expected_url = "https://finviz.com/chart.ashx?t=SPY&ty=c&ta=1&p=d"
    chart_url = utils.get_stock_chart("SPY")
    assert chart_url == expected_url


def test_get_symbol_details(mocker):
    """Verify getting stock data."""
    mocked_class = mocker.patch(target="thetagang_notifications.utils.yf.Ticker")
    utils.get_symbol_details("AMD")
    mocked_class.assert_called_with("AMD")

    mocked_class = mocker.patch(
        target="thetagang_notifications.utils.yf.Ticker",
        side_effect=Exception("something broke"),
    )
    with pytest.raises(Exception) as excinfo:
        utils.get_symbol_details("AMD")
        mocked_class.assert_called_with("AMD")
        assert excinfo.value.message == "something broke"
