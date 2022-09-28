"""Tests for trades functions."""
from freezegun import freeze_time
import pytest
import requests

from thetagang_notifications import config, trades
from thetagang_notifications.trades import Trade

# Example trade GUIDs from thetagang.com.
CASH_SECURED_PUT = "c90e5d5d-8158-43d7-ba09-e6a0dbbf207c"
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


@pytest.mark.vcr()
def test_download_trades():
    """Test downloading a list of trades."""
    trade_list = trades.download_trades()
    assert isinstance(trade_list, list)
    assert len(trade_list) == 100
    assert "type" in trade_list[0].keys()


@pytest.mark.vcr()
def test_trades_main(mocker):
    """Test main() in trades module."""
    trade_class = mocker.patch(target="thetagang_notifications.trades.Trade")
    trades.main()
    trade_class.assert_called()


def test_closed_trade():
    """Test a closed trade."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))

    # It shouldn't be closed now because it's brand new.
    assert not res.is_recently_closed

    # Capture the closed date and remove it from the trade.
    close_date = res.trade['close_date']
    res.trade['close_date'] = None

    # Save the trade as a new trade.
    res.save()

    # This shouldn't be a closed trade (yet).
    assert not res.is_recently_closed

    # Mark it as closed.
    res.trade['close_date'] = close_date

    # It should now be closed.
    assert res.is_recently_closed


@pytest.mark.vcr()
@freeze_time("2022-02-10")
def test_cash_secured_put(mocker):
    """Test notification with a cash secured put."""
    res = Trade(get_theta_trade(CASH_SECURED_PUT))
    assert res.breakeven == "438.60"
    assert res.guid == "c90e5d5d-8158-43d7-ba09-e6a0dbbf207c"
    assert res.pretty_expiration == "2/18"
    assert res.is_option_trade
    assert res.is_patron_trade
    assert res.is_single_option
    assert res.is_short
    assert res.quantity == 1
    assert res.raw_strikes == "$440"
    assert res.short_return == 0.32
    assert res.short_return_annualized == 12.98
    assert res.strike == "440"
    assert res.symbol == "SPY"
    assert res.symbol_logo.endswith("SPY.png")
    assert res.trade_type == "CASH SECURED PUT"
    assert res.username == "mhayden"

    mock_exec = mocker.patch(
        target="thetagang_notifications.trades.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_TRADES
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "SPY: CASH SECURED PUT\n1 x 2/18 $440p for $1.40"
    assert embed["thumbnail"]["url"] == res.symbol_logo

    mock_exec.assert_called_once()


@pytest.mark.vcr()
@freeze_time("2022-02-10")
def test_covered_call(mocker):
    """Test notification with a covered call."""
    res = Trade(get_theta_trade(COVERED_CALL))
    assert res.breakeven == "461.30"
    assert res.guid == "2093163e-2d7b-424f-b007-51c46ace7bb4"
    assert res.pretty_expiration == "2/18"
    assert res.is_option_trade
    assert res.is_patron_trade
    assert res.is_single_option
    assert res.is_short
    assert res.quantity == 1
    assert res.raw_strikes == "$460"
    assert res.short_return == 0.28
    assert res.short_return_annualized == 11.36
    assert res.strike == "460"
    assert res.symbol == "SPY"
    assert res.symbol_logo.endswith("SPY.png")
    assert res.trade_type == "COVERED CALL"
    assert res.username == "mhayden"

    mock_exec = mocker.patch(
        target="thetagang_notifications.trades.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_TRADES
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "SPY: COVERED CALL\n1 x 2/18 $460c for $1.30"
    assert embed["thumbnail"]["url"] == res.symbol_logo

    mock_exec.assert_called_once()


@pytest.mark.vcr()
@freeze_time("2021-08-01")
def test_put_credit_spread(mocker):
    """Test notification with a put credit spread."""
    res = Trade(get_theta_trade(PUT_CREDIT_SPREAD))
    assert not res.breakeven
    assert res.guid == "7a9fe9d3-b1aa-483c-bcc0-b6f73c6b4eec"
    assert res.pretty_expiration == "9/17"
    assert res.is_option_trade
    assert res.is_patron_trade
    assert not res.is_single_option
    assert res.is_short
    assert res.quantity == 1
    assert res.raw_strikes == "$170/$175"
    assert not res.short_return
    assert not res.short_return_annualized
    assert not res.strike
    assert res.symbol == "DIS"
    assert res.symbol_logo.endswith("DIS.png")
    assert res.trade_type == "PUT CREDIT SPREAD"
    assert res.username == "mhayden"

    mock_exec = mocker.patch(
        target="thetagang_notifications.trades.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_TRADES
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "DIS: PUT CREDIT SPREAD\n1 x 9/17 $170/$175 for $1.54"
    assert embed["thumbnail"]["url"] == res.symbol_logo

    mock_exec.assert_called_once()


@pytest.mark.vcr()
@freeze_time("2022-02-10")
def test_buy_common_stock(mocker):
    """Test notification with stock purchase."""
    res = Trade(get_theta_trade(BUY_COMMON_STOCK))
    assert not res.breakeven
    assert res.guid == "72060eaa-7803-4124-be5b-c03b54171e75"
    assert not res.parse_expiration()
    assert not res.pretty_expiration
    assert not res.is_option_trade
    assert res.is_patron_trade
    assert not res.is_single_option
    assert not res.is_short
    assert res.quantity == 100
    assert not res.raw_strikes
    assert not res.short_return
    assert not res.short_return_annualized
    assert not res.strike
    assert res.symbol == "SPY"
    assert res.symbol_logo.endswith("SPY.png")
    assert res.trade_type == "BUY COMMON STOCK"
    assert res.username == "mhayden"

    mock_exec = mocker.patch(
        target="thetagang_notifications.trades.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_TRADES
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "SPY: BUY COMMON STOCK\n100 share(s) at $456.91"
    assert embed["thumbnail"]["url"] == res.symbol_logo

    mock_exec.assert_called_once()


@pytest.mark.vcr()
@freeze_time("2021-08-01")
def test_short_iron_condor(mocker):
    """Test notification with a put credit spread."""
    res = Trade(get_theta_trade(SHORT_IRON_CONDOR))
    assert not res.breakeven
    assert res.guid == "8cdf95fd-d0d4-4f47-ae81-a1e000979291"
    assert res.pretty_expiration == "3/18"
    assert res.is_option_trade
    assert res.is_patron_trade
    assert not res.is_single_option
    assert res.is_short
    assert res.quantity == 1
    assert res.raw_strikes == "$110/$115/$150/$155"
    assert not res.short_return
    assert not res.short_return_annualized
    assert not res.strike
    assert res.symbol == "PYPL"
    assert res.symbol_logo.endswith("PYPL.png")
    assert res.trade_type == "SHORT IRON CONDOR"
    assert res.username == "Rustyerr"

    mock_exec = mocker.patch(
        target="thetagang_notifications.trades.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_TRADES
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == (
        f"{res.symbol}: {res.trade_type}\n"
        f"{res.quantity} x {res.pretty_expiration} {res.raw_strikes} "
        f"for {res.pretty_premium}"
    )
    assert embed["thumbnail"]["url"] == res.symbol_logo

    mock_exec.assert_called_once()

    # Also verify that we don't alert for the same trade twice.
    mock_exec.reset_mock()
    res.notify()
    mock_exec.assert_not_called()


@pytest.mark.vcr()
@freeze_time("2022-02-10")
def test_non_patron_trade(mocker):
    """Test a trade made by a non-patron user."""
    res = Trade(get_theta_trade(NON_PATRON_TRADE))
    assert not res.is_patron_trade

    mock_exec = mocker.patch(
        target="thetagang_notifications.trades.DiscordWebhook.execute"
    )
    res.notify()
    mock_exec.assert_not_called()
