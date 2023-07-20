"""Tests for utils functions."""
from unittest.mock import MagicMock, patch

import pytest
import requests_mock

from thetagang_notifications import utils


class TestUtils:
    """Test the utils module."""

    @pytest.mark.vcr
    def test_get_stock_logo(self) -> None:
        """Test getting a stock logo."""
        result = utils.get_stock_logo("AMD")
        assert "AMD.png" in result

    @pytest.mark.vcr
    def test_get_stock_logo_failure(self, mocker):
        """Test getting a stock logo when everything fails."""
        result = utils.get_stock_logo("DOOTY")
        assert result is None

    def test_get_stock_logo_success(self, requests_mock, mocker):
        """Test getting a stock logo when everything fails."""
        primary_url = f"{utils.IEX_PRIMARY_LOGO_URL}/AMD.png"
        secondary_url = f"{utils.IEX_SECONDARY_LOGO_URL}/AMD.png"
        requests_mock.get(primary_url, headers={"x-goog-hash": utils.IEX_PLACEHOLDER_IMAGE_HASH})
        requests_mock.get(secondary_url, text="doot")
        mocker.patch(target="thetagang_notifications.utils.get_logo_clearbit", return_value=None)
        result = utils.get_stock_logo("AMD")
        assert result == secondary_url

    def test_get_base_domain(self):
        """Verify we can get a base domain."""
        assert utils.get_base_domain("gsdgsdfg.sdfgdsfgsd.google.com") == "google.com"
        assert utils.get_base_domain("wheeeee.google.co.uk") == "google.co.uk"

    def test_get_logo_iex_403(
        self,
    ):
        """Test retrieving logos from IEX."""
        with requests_mock.Mocker() as mock_req:
            url = f"{utils.IEX_PRIMARY_LOGO_URL}/AMD.png"
            mock_req.get(url, status_code=403)
            result = utils.get_logo_iex(url)
            assert result is None

    def test_get_logo_iex_placeholder(
        self,
    ):
        """Test retrieving logos from IEX."""
        with requests_mock.Mocker() as mock_req:
            url = f"{utils.IEX_PRIMARY_LOGO_URL}/AMD.png"
            mock_req.get(url, headers={"x-goog-hash": utils.IEX_PLACEHOLDER_IMAGE_HASH})
            result = utils.get_logo_iex(url)
            assert result is None

    @patch("thetagang_notifications.utils.website_for_symbol")
    def test_get_logo_clearbit(self, mock_website_for_symbol: MagicMock) -> None:
        """Test retrieving logos from Clearbit."""
        mock_website_for_symbol.return_value = "https://amd.com"

        result = utils.get_logo_clearbit("AMD")
        assert result == "https://logo.clearbit.com/amd.com"
