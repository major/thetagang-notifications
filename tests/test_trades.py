"""Tests for trades functions."""
import json

from freezegun import freeze_time
import requests_mock

from thetagang_notifications import config, trades


def load_asset(asset_filename):
    """Load an asset from test assets."""
    with open(f"tests/assets/{asset_filename}", "r") as fileh:
        return json.load(fileh)


@requests_mock.Mocker(kw="mock")
def test_download_trades(**kwargs):
    """Ensure we handle downloaded trades properly."""
    mocked_json = {"data": {"trades": ["a trade would be here!"]}}
    kwargs["mock"].get(config.TRADES_JSON_URL, json=mocked_json)

    downloaded_trades = trades.download_trades()
    assert downloaded_trades[0] == "a trade would be here!"


@freeze_time("2022-02-03")
def test_parse_trade_cash_secured_put():
    """Ensure we can parse a cash secured put."""
    trade = load_asset("trade-cash-secured-put.json")
    result = trades.parse_trade(trade)
    assert result["strike"] == "$85"
    assert result["breakeven"] == 83.2
    assert result["return"] == 2.1634615384615383
    assert result["annualized_return"] == 52.64423076923077


@freeze_time("2022-02-03")
def test_parse_trade_covered_call():
    """Ensure we can parse a covered call."""
    trade = load_asset("trade-covered-call.json")
    result = trades.parse_trade(trade)
    print(json.dumps(result, indent=2))
    assert result["strike"] == "$145"
    assert result["breakeven"] == 145.92


def test_parse_trade_short_naked_call():
    """Ensure we can parse a short naked call."""
    trade = load_asset("trade-short-naked-call.json")
    result = trades.parse_trade(trade)
    assert result["strikes"] == "$465"


def test_parse_trade_call_credit_spread():
    """Ensure we can parse a call credit spread."""
    trade = load_asset("trade-call-credit-spread.json")
    result = trades.parse_trade(trade)
    assert result["strikes"] == "$137/$140"


def test_parse_trade_put_credit_spread():
    """Ensure we can parse a put credit spread."""
    trade = load_asset("trade-put-credit-spread.json")
    result = trades.parse_trade(trade)
    assert result["strikes"] == "$145/$140"


def test_parse_trade_put_short_iron_condor():
    """Ensure we can parse a short iron condor."""
    trade = load_asset("trade-short-iron-condor.json")
    result = trades.parse_trade(trade)
    assert result["strikes"] == "$123/$120/$140/$137"
