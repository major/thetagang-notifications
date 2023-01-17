"""Tests for trades functions."""
import pytest
import requests
from freezegun import freeze_time

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
LONG_NAKED_PUT = "19a3beee-95e9-4c19-ab1d-712793f3eeaf"
SHORT_NAKED_CALL = "665b5d15-7009-49b7-8746-0e7effdf0829"
NON_PATRON_TRADE = "36ad8e04-b2a1-40c8-8632-55e491be10ca"


def get_theta_trade(guid):
    """Get an example thetagang.com trade from the site."""
    url = f"https://api.thetagang.com/trades/{guid}"
    return requests.get(url).json()["data"]["trade"]


@freeze_time("2022-01-01")
@pytest.mark.vcr()
def test_dte():
    """Test the DTE calculation."""
    trade = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert trade.dte == 49


@pytest.mark.vcr()
def test_is_assigned():
    """Test that the trade is assigned."""
    trade = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert trade.is_assigned


@pytest.mark.vcr()
def test_is_closed():
    """Test if a trade is closed."""
    trade = Trade(get_theta_trade(CLOSED_CASH_SECURED_PUT))
    assert trade.is_closed

    trade.trade["close_date"] = None
    assert not trade.is_closed


@pytest.mark.vcr()
def test_is_option_trade():
    """Test is_option_trade."""
    trade = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert trade.is_option_trade

    trade = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert not trade.is_option_trade


@pytest.mark.vcr()
def test_is_single_leg():
    """Test single leg trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.is_single_leg is True


@pytest.mark.vcr()
def test_is_multiple_leg():
    """Test a multiple leg trade."""
    res = Trade(get_theta_trade(SHORT_IRON_CONDOR))
    assert res.is_multiple_leg is True


@pytest.mark.vcr()
def test_is_short():
    """Test a short trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.is_short is True

    res = Trade(get_theta_trade(LONG_NAKED_PUT))
    assert res.is_short is False


@pytest.mark.vcr()
def test_is_winner():
    """Test a winning trade."""
    res = Trade(get_theta_trade(CLOSED_CASH_SECURED_PUT))
    assert res.is_winner


@pytest.mark.vcr()
def test_note():
    """Test getting a trade note."""
    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.note == res.trade["note"]

    res = Trade(get_theta_trade(CLOSED_CASH_SECURED_PUT))
    assert res.note == res.trade["closing_note"]


@pytest.mark.vcr()
def test_parse_expiration():
    """Test parsing the expiration date."""
    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.parse_expiration() is None


@freeze_time("2022-01-01")
@pytest.mark.vcr()
def test_pretty_expiration():
    """Test pretty parsing an expiration date."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.pretty_expiration == "2/18"


@freeze_time("2020-01-01")
@pytest.mark.vcr()
def test_pretty_expiration_far_away():
    """Test pretty parsing an expiration date that is far away."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.pretty_expiration == "2/18/22"


@pytest.mark.vcr()
def test_pretty_expiration_invalid():
    """Test pretty parsing an invalid trade."""
    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.pretty_expiration is None


@pytest.mark.vcr()
def test_pretty_premium():
    """Test pretty parsing a premium."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.pretty_premium == "$1.40"


@pytest.mark.vcr()
def test_quantity():
    """Test the quantity of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.quantity == 1


@pytest.mark.vcr()
def test_guid():
    """Test the GUID of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.guid == CASH_SECURED_PUT


@pytest.mark.vcr()
def test_raw_strikes():
    """Test the raw strikes of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.raw_strikes == "$440"

    res = Trade(get_theta_trade(SHORT_IRON_CONDOR))
    assert res.raw_strikes == "$110/$115/$150/$155"

    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.raw_strikes is None


@pytest.mark.vcr()
def test_short_return():
    """Test the short return of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.short_return == 0.32

    res = Trade(get_theta_trade(CLOSED_CASH_SECURED_PUT))
    assert res.short_return == 1.1

    res = Trade(get_theta_trade(SHORT_NAKED_CALL))
    assert res.short_return == 0.86

    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.short_return is None


@freeze_time("2022-01-01")
@pytest.mark.vcr()
def test_short_return_annualized():
    """Test the short return of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.short_return_annualized == 2.38

    res = Trade(get_theta_trade(CLOSED_CASH_SECURED_PUT))
    assert res.short_return_annualized == 1.47

    res = Trade(get_theta_trade(SHORT_NAKED_CALL))
    assert res.short_return_annualized == 0.85

    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.short_return_annualized is None


@pytest.mark.vcr()
def test_status():
    """Test the status of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.status == "closed"

    res.trade["close_date"] = None
    assert res.status == "open"

    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.status == "closed"


@pytest.mark.vcr()
def test_strike():
    """Test the strike of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.strike == "440"

    res = Trade(get_theta_trade(SHORT_IRON_CONDOR))
    assert res.strike is None

    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.strike is None


@pytest.mark.vcr()
def test_symbol():
    """Test the symbol of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.symbol == "SPY"

    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.symbol == "SPY"


@pytest.mark.vcr()
def test_trade_url():
    """Test the trade URL of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.trade_url == f"https://thetagang.com/{res.username}/{res.guid}"


@pytest.mark.vcr()
def test_username():
    """Test the username of a trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.username == "mhayden"

    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert res.username == "mhayden"
