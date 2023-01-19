"""Test discord notifications for trades."""
from unittest import mock

import pytest
from discord_webhook import DiscordEmbed

from thetagang_notifications import notification
from thetagang_notifications.config import CLOSING_TRADE_ICON
from thetagang_notifications.trade import get_handler as trade_get_handler


@pytest.mark.block_network
@pytest.mark.parametrize("real_trades", ["CASH SECURED PUT"], indirect=True)
def test_generate_action(real_trades):
    """Test generate action."""
    trade_obj = trade_get_handler(real_trades)
    test_notifier = notification.get_handler(trade_obj)
    action = test_notifier.generate_action()

    assert action["name"] == f"{trade_obj.username} closed a trade"
    assert action["icon_url"] == CLOSING_TRADE_ICON
    assert (
        action["url"] == f"https://thetagang.com/{trade_obj.username}/{trade_obj.guid}"
    )


@pytest.mark.block_network
def test_generate_description(real_trades):
    """Test generate description."""
    trade_obj = trade_get_handler(real_trades)
    test_notifier = notification.get_handler(trade_obj)
    desc = test_notifier.generate_description()

    assert desc == "Sample description"


@pytest.mark.block_network
def test_generate_embeds(real_trades):
    """Test generate embeds."""
    trade_obj = trade_get_handler(real_trades)
    test_notifier = notification.get_handler(trade_obj)
    with mock.patch("thetagang_notifications.notification.get_stock_logo"):
        embed = test_notifier.generate_embeds()

    assert isinstance(embed, DiscordEmbed)


@pytest.mark.block_network
@pytest.mark.parametrize("real_trades", ["CASH SECURED PUT"], indirect=True)
def test_notify(real_trades):
    """Test notify."""
    trade_obj = trade_get_handler(real_trades)
    test_notifier = notification.get_handler(trade_obj)

    with mock.patch(
        "thetagang_notifications.notification.DiscordWebhook.execute"
    ) as mock_execute, mock.patch(
        "thetagang_notifications.notification.get_stock_logo"
    ) as mock_logo:
        mock_logo.return_value = "https://storage.googleapis.com/iex/api/logos/SPY.png"
        test_notifier.generate_embeds()
        test_notifier.notify()

    assert mock_execute.called_once()
