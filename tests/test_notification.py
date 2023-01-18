"""Test discord notifications for trades."""
import pytest

from thetagang_notifications.config import CLOSING_TRADE_ICON
from thetagang_notifications.notification import ClosingNotification
from thetagang_notifications.trades import Trade


@pytest.mark.parametrize("real_trades", ["CASH SECURED PUT"], indirect=True)
def test_closing_notification(real_trades):
    """Test closing notification."""
    trade = Trade(real_trades)
    notification = ClosingNotification(trade)
    assert notification.action_line() == {
        "name": f"{trade.username} closed a trade",
        "url": trade.trade_url,
        "icon_url": CLOSING_TRADE_ICON,
    }
