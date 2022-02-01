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
    today = datetime.now()
    expiration = "2022-03-18T00:00:00.000Z"
    expected_dte = 45
    assert utils.get_dte(expiration) == expected_dte
