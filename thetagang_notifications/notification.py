"""Send notifications to discord for trades."""
from abc import ABC, abstractmethod

from thetagang_notifications.config import CLOSING_TRADE_ICON, OPENING_TRADE_ICON


class Notification(ABC):
    """Base class for discord notifications."""

    def __init__(self, trade):
        """Initialization method."""
        self.trade = trade

    @abstractmethod
    def action_line(self):
        """Generate an action line for the top of the trade notification."""
        raise NotImplementedError


class OpeningNotification(Notification):
    """Handle opening notifications."""

    def __init__(self, trade):
        """Initialization method."""
        super().__init__(trade)

    def action_line(self):
        """Generate an action line for the top of the trade notification."""
        return {
            "name": f"{self.trade.username} opened a trade",
            "url": self.trade.trade_url,
            "icon_url": OPENING_TRADE_ICON,
        }


class ClosingNotification(Notification):
    """Handle closing notifications."""

    def __init__(self, trade):
        """Initialization method."""
        super().__init__(trade)

    def action_line(self):
        """Generate an action line for the top of the trade notification."""
        return {
            "name": f"{self.trade.username} closed a trade",
            "url": self.trade.trade_url,
            "icon_url": CLOSING_TRADE_ICON,
        }
