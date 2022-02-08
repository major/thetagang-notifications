"""Tests for utils functions."""
from datetime import datetime
import json

from freezegun import freeze_time
import pytest
import requests_mock


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


def test_breakeven_unknown():
    """Test breakevens when we can't calculate them."""
    trade = load_trade_asset("trade-short-iron-condor.json")
    assert utils.get_breakeven(trade) is None


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


def test_get_logo():
    """Ensure we generate a stock logo properly."""
    assert utils.get_logo("AMD").endswith("AMD.png")
    assert utils.get_logo("sPy").endswith("SPY.png")


def test_get_finviz_stock_equity(mocker):
    """Ensure we get stock data from finviz properly."""
    mocker.patch(
        target="thetagang_notifications.utils.finviz.get_stock",
        return_value=load_trade_asset("finviz-amd.json"),
    )
    result = utils.get_finviz_stock("AMD")
    assert result["Website"] == "https://www.amd.com"
    assert result["Sector"] == "Technology"


def test_get_finviz_stock_etf(mocker):
    """Ensure we get stock data from finviz properly."""
    mocker.patch(
        target="thetagang_notifications.utils.finviz.get_stock",
        return_value=load_trade_asset("finviz-soxl.json"),
    )
    result = utils.get_finviz_stock("AMD")
    assert result["Website"] is None
    assert result["Sector"] == "Exchange Traded Fund"


def test_get_stock_logo_failure(mocker):
    """Test getting a stock logo when everything fails."""
    mocker.patch(target="thetagang_notifications.utils.get_logo_iex", return_value=None)
    mocker.patch(
        target="thetagang_notifications.utils.get_logo_clearbit", return_value=None
    )
    result = utils.get_stock_logo("AMD")
    assert result is None


def test_get_stock_logo_success(requests_mock, mocker):
    """Test getting a stock logo when everything fails."""
    primary_url = f"{utils.IEX_PRIMARY_LOGO_URL}/AMD.png"
    secondary_url = f"{utils.IEX_SECONDARY_LOGO_URL}/AMD.png"
    requests_mock.get(
        primary_url, headers={"x-goog-hash": utils.IEX_PLACEHOLDER_IMAGE_HASH}
    )
    requests_mock.get(secondary_url, text="doot")
    mocker.patch(
        target="thetagang_notifications.utils.get_logo_clearbit", return_value=None
    )
    result = utils.get_stock_logo("AMD")
    from pprint import pprint

    pprint(result)
    assert result == secondary_url


def test_get_finviz_stock_failure(mocker):
    """Ensure we get stock data from finviz properly."""
    mocked_class = mocker.patch(
        target="thetagang_notifications.utils.finviz.get_stock",
        side_effect=Exception("something broke"),
    )
    with pytest.raises(Exception) as excinfo:
        utils.get_finviz_stock("DOOT")
        mocked_class.assert_called_with("DOOT")
        assert excinfo.value.message == "something broke"


def test_get_base_domain():
    """Verify we can get a base domain."""
    assert utils.get_base_domain("gsdgsdfg.sdfgdsfgsd.google.com") == "google.com"
    assert utils.get_base_domain("wheeeee.google.co.uk") == "google.co.uk"


def test_get_logo_iex_403():
    """Test retrieving logos from IEX."""
    with requests_mock.Mocker() as mock_req:
        url = f"{utils.IEX_PRIMARY_LOGO_URL}/AMD.png"
        mock_req.get(url, status_code=403)
        result = utils.get_logo_iex(url)
        assert result is None


def test_get_logo_iex_placeholder():
    """Test retrieving logos from IEX."""
    with requests_mock.Mocker() as mock_req:
        url = f"{utils.IEX_PRIMARY_LOGO_URL}/AMD.png"
        mock_req.get(url, headers={"x-goog-hash": utils.IEX_PLACEHOLDER_IMAGE_HASH})
        result = utils.get_logo_iex(url)
        assert result is None


def test_get_logo_clearbit(mocker):
    """Ensure we get a logo from clearbit."""
    # Try it with a complete URL first.
    amd_data = load_trade_asset("finviz-amd.json")
    mocker.patch(
        target="thetagang_notifications.utils.finviz.get_stock",
        return_value=amd_data,
    )
    result = utils.get_logo_clearbit("AMD")
    assert result == "https://logo.clearbit.com/amd.com"

    # Now try it without a URL.
    soxl_data = load_trade_asset("finviz-soxl.json")
    mocker.patch(
        target="thetagang_notifications.utils.finviz.get_stock",
        return_value=soxl_data,
    )
    result = utils.get_logo_clearbit("SOXL")
    assert result is None


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
