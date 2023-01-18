"""Test discord notifications for trades."""
from thetagang_notifications.config import CLOSING_TRADE_ICON, OPENING_TRADE_ICON
from thetagang_notifications.notification import (
    ClosingNotification,
    OpeningNotification,
)
from thetagang_notifications.trades import Trade


def test_opening_notification(cash_secured_put):
    """Test opening notification."""
    trade = Trade(cash_secured_put)
    notification = OpeningNotification(trade)
    assert notification.action_line() == {
        "name": f"{trade.username} opened a trade",
        "url": trade.trade_url,
        "icon_url": OPENING_TRADE_ICON,
    }


def test_closing_notification(cash_secured_put):
    """Test closing notification."""
    trade = Trade(cash_secured_put)
    notification = ClosingNotification(trade)
    assert notification.action_line() == {
        "name": f"{trade.username} closed a trade",
        "url": trade.trade_url,
        "icon_url": CLOSING_TRADE_ICON,
    }
