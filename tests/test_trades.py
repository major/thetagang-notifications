"""Tests for trades functions."""
import requests

from thetagang_notifications.trades import Trade

# Example trade GUIDs from thetagang.com.
CASH_SECURED_PUT = "c90e5d5d-8158-43d7-ba09-e6a0dbbf207c"
CLOSED_CASH_SECURED_PUT = "af55de42-a4b0-469d-a20d-faacc63edf6c"
CLOSED_CASH_SECURED_PUT_LOSS = "f16e80c3-9daa-4e14-863a-8416d4107de6"
COVERED_CALL = "2093163e-2d7b-424f-b007-51c46ace7bb4"
PUT_CREDIT_SPREAD = "7a9fe9d3-b1aa-483c-bcc0-b6f73c6b4eec"
SHORT_IRON_CONDOR = "8cdf95fd-d0d4-4f47-ae81-a1e000979291"
BUY_COMMON_STOCK = "72060eaa-7803-4124-be5b-c03b54171e75"
SELL_COMMON_STOCK = "a2a46a7f-1c7c-4328-98d7-32b900af98c1"
NON_PATRON_TRADE = "36ad8e04-b2a1-40c8-8632-55e491be10ca"


def get_theta_trade(guid):
    """Get an example thetagang.com trade from the site."""
    url = f"https://api.thetagang.com/trades/{guid}"
    return requests.get(url).json()["data"]["trade"]


def test_is_single_leg():
    """Test single leg trade."""
    res = Trade({"type": "COVERED CALL"})
    assert res.is_single_leg


def test_not_single_leg():
    """Test a multiple leg trade."""
    res = Trade({"type": "SHORT STRANGLE"})
    assert not res.is_single_leg


def test_is_multiple_leg():
    """Test a multiple leg trade."""
    res = Trade({"type": "SHORT STRANGLE"})
    assert res.is_multiple_leg


def test_is_not_multiple_leg():
    """Test a single leg trade."""
    res = Trade({"type": "COVERED CALL"})
    assert not res.is_multiple_leg
