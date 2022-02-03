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


def test_parse_trade_buy_common_stock():
    """Ensure we can parse a buy common stock trade."""
    trade = load_asset("trade-buy-common-stock.json")
    result = trades.parse_trade(trade)
    assert result is None


def test_get_webhook_color():
    """Verify that we determine the right webhook colors."""
    assert trades.get_webhook_color("CASH SECURED PUT") == "299617"
    assert trades.get_webhook_color("SHORT NAKED CALL") == "FD3A4A"
    assert trades.get_webhook_color("SHORT STRANGLE") == "BFAFB2"


def test_get_trade_url():
    """Ensure we generate trade URLs properly."""
    trade = {
        "User": {"username": "Tester"},
        "guid": "82ea7953-cdfb-4a4d-a381-f2a39c87c401",
    }
    result = trades.get_trade_url(trade)
    assert result == "https://thetagang.com/Tester/82ea7953-cdfb-4a4d-a381-f2a39c87c401"


def test_notify_short_call(mocker):
    """Verify that short call notifications are set up properly."""
    config.WEBHOOK_URL_TRADES = "https://example_webhook_url"
    mocker.patch("thetagang_notifications.trades.DiscordEmbed")
    mock_send = mocker.patch("thetagang_notifications.trades.send_webhook")

    trade = load_asset("trade-covered-call.json")
    norm = trades.parse_short_call(trade)

    trades.notify_trade(trade, norm, {})
    mock_send.assert_called_once()

    mock_send.reset_mock()
    trades.notify_trade(trade, norm, {"logo_url": "http://example.com/example.png"})
    mock_send.assert_called_once()


def test_notify_short_put(mocker):
    """Verify that short put notifications are set up properly."""
    config.WEBHOOK_URL_TRADES = "https://example_webhook_url"
    mocker.patch("thetagang_notifications.trades.DiscordEmbed")
    mock_send = mocker.patch("thetagang_notifications.trades.send_webhook")

    trade = load_asset("trade-cash-secured-put.json")
    norm = trades.parse_short_put(trade)

    trades.notify_trade(trade, norm, {})
    mock_send.assert_called_once()

    mock_send.reset_mock()
    trades.notify_trade(trade, norm, {"logo_url": "http://example.com/example.png"})
    mock_send.assert_called_once()


def test_notify_generic_trade(mocker):
    """Verify that generic trade notifications are set up properly."""
    config.WEBHOOK_URL_TRADES = "https://example_webhook_url"
    mocker.patch("thetagang_notifications.trades.DiscordEmbed")
    mock_send = mocker.patch("thetagang_notifications.trades.send_webhook")

    trade = load_asset("trade-short-iron-condor.json")
    norm = trades.parse_generic_trade(trade)

    trades.notify_trade(trade, norm, {})
    mock_send.assert_called_once()

    mock_send.reset_mock()
    trades.notify_trade(trade, norm, {"logo_url": "http://example.com/example.png"})
    mock_send.assert_called_once()


def test_notify_stock_trade(mocker):
    """Verify that stock trade notifications are set up properly."""
    config.WEBHOOK_URL_TRADES = "https://example_webhook_url"
    mocker.patch("thetagang_notifications.trades.DiscordEmbed")
    mock_send = mocker.patch("thetagang_notifications.trades.send_webhook")

    trade = load_asset("trade-buy-common-stock.json")
    norm = trades.parse_generic_trade(trade)

    trades.notify_trade(trade, norm, {})
    mock_send.assert_called_once()

    mock_send.reset_mock()
    trades.notify_trade(trade, norm, {"logo_url": "http://example.com/example.png"})
    mock_send.assert_called_once()


def test_send_webhook(mocker):
    """Verify that sending webhooks works properly."""
    mock_hook = mocker.patch("thetagang_notifications.trades.DiscordWebhook")
    mock_embed = mocker.patch("thetagang_notifications.trades.DiscordEmbed")

    trades.send_webhook(None)
    mock_hook.assert_called_with(
        url=config.WEBHOOK_URL_TRADES,
        rate_limit_retry=True,
        username=config.DISCORD_USERNAME,
    )

    trades.send_webhook(mock_embed)
    mock_hook.assert_called_with(
        url=config.WEBHOOK_URL_TRADES,
        rate_limit_retry=True,
        username=config.DISCORD_USERNAME,
    )


def test_handle_trade(mocker):
    """Test handle_trade."""
    mock_parse = mocker.patch(
        "thetagang_notifications.trades.parse_trade", return_value="normalized_data"
    )
    mock_details = mocker.patch(
        "thetagang_notifications.utils.get_symbol_details",
        return_value="company_details",
    )
    mock_notify = mocker.patch("thetagang_notifications.trades.notify_trade")

    trade = load_asset("trade-call-credit-spread.json")
    trades.handle_trade(trade)

    mock_parse.assert_called_once()
    mock_parse.assert_called_with(trade)
    mock_details.assert_called_once()
    mock_details.assert_called_with(trade["symbol"])
    mock_notify.assert_called_once()
    mock_notify.assert_called_with(trade, "normalized_data", "company_details")


def test_handle_trade_exclude_non_patron(mocker):
    """Test handle_trade when we are excluding patron trades."""
    trade = {"User": {"role": "member"}}
    config.PATRON_TRADES_ONLY = True
    result = trades.handle_trade(trade)
    assert result is None
