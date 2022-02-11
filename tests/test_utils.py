"""Tests for utils functions."""
import pytest
import requests_mock


from thetagang_notifications import utils


def test_get_stock_chart():
    """Ensure we can get a chart URL."""
    expected_url = "https://finviz.com/chart.ashx?t=SPY&ty=c&ta=1&p=d"
    chart_url = utils.get_stock_chart("SPY")
    assert chart_url == expected_url


@pytest.mark.vcr()
def test_get_finviz_stock_equity():
    """Ensure we get stock data from finviz properly."""
    result = utils.get_finviz_stock("AMD")
    assert result["Website"] == "https://www.amd.com"
    assert result["Sector"] == "Technology"


@pytest.mark.vcr()
def test_get_finviz_stock_etf():
    """Ensure we get stock data from finviz properly."""
    result = utils.get_finviz_stock("SOXL")
    assert not result["Website"]
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


@pytest.mark.vcr()
def test_get_logo_clearbit(mocker):
    """Ensure we get a logo from clearbit."""
    result = utils.get_logo_clearbit("AMD")
    assert result == "https://logo.clearbit.com/amd.com"

    result = utils.get_logo_clearbit("SOXL")
    assert result is None

    result = utils.get_logo_clearbit("DOOTS")
    assert result is None
