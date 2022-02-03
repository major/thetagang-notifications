"""Tests for utils functions."""
from datetime import datetime
import json

from freezegun import freeze_time
import pytest


from thetagang_notifications import utils


def load_trade_asset(asset_filename):
    """Load a trade asset from test assets."""
    with open(f"tests/assets/{asset_filename}", "r") as fileh:
        return json.load(fileh)


def test_breakeven_short_put():
    """Test short option breakevens."""
    trade = {"type": "CASH SECURED PUT", "short_put": "100", "price_filled": 1.50}
    assert utils.get_breakeven(trade) == 98.50


def test_breakeven_covered_call():
    """Test short option breakevens."""
    trade = {"type": "COVERED CALL", "short_call": "100", "price_filled": 1.50}
    assert utils.get_breakeven(trade) == 101.50


def test_breakeven_short_call():
    """Test short option breakevens."""
    trade = {"type": "SHORT NAKED CALL", "short_call": "100", "price_filled": 1.50}
    assert utils.get_breakeven(trade) == 101.50


@freeze_time("2022-02-03")
def test_short_put_return():
    """Verify that we calculate put breakevens correctly."""
    trade = {
        "short_put": 190,
        "price_filled": 1.73,
        "expiry_date": "2022-02-18T00:00:00.000Z",
    }
    result = utils.get_short_put_return(trade)
    assert result == 0.918893079088543


@freeze_time("2022-02-03")
def test_short_call_return():
    """Verify that we calculate call breakevens correctly."""
    trade = load_trade_asset("trade-covered-call.json")
    print(trade)
    result = utils.get_short_call_return(trade)
    assert result == 0.6385341476957246


def test_gather_strikes():
    """Ensure we can gather strikes in a generic way."""
    trade = load_trade_asset("trade-short-iron-condor.json")
    strikes = utils.gather_strikes(trade)
    assert strikes == "$123/$120/$140/$137"


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


def test_get_pretty_expiration_no_date():
    """Test a pretty expiration parse with no expiration date (buying stocks)."""
    assert utils.get_pretty_expiration(None) is None


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
