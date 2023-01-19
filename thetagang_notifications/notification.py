"""Send notifications to discord for trades."""

from abc import ABC

from discord_webhook import DiscordEmbed, DiscordWebhook

from thetagang_notifications.config import (
    CLOSING_TRADE_ICON,
    DISCORD_USERNAME,
    OPENING_TRADE_ICON,
    TRANSPARENT_PNG,
    WEBHOOK_URL_TRADES,
)
from thetagang_notifications.utils import get_stock_logo


class Notification(ABC):
    """Base class for discord notifications."""

    def __init__(self, trade):
        """Initialization method."""
        self.trade = trade
        self.trade_note = (
            self.trade.note if self.trade.is_open else self.trade.closing_note
        )

    def generate_action(self):
        """Generate the action for the notification."""
        return {
            "name": f"{self.trade.username} {self.trade.status} a trade",
            "icon_url": OPENING_TRADE_ICON
            if self.trade.is_open
            else CLOSING_TRADE_ICON,
            "url": f"https://thetagang.com/{self.trade.username}/{self.trade.guid}",
        }

    def generate_description(self):
        """Generate the description for the notification."""
        return "Sample description"

    def generate_embeds(self):
        """Generate the embeds for the notification."""
        embed = DiscordEmbed(
            title=f"${self.trade.symbol}: {self.trade.trade_type}",
            description=self.generate_description(),
        )
        embed.set_author(**self.generate_action())
        embed.set_image(url=TRANSPARENT_PNG)
        embed.set_thumbnail(url=get_stock_logo(self.trade.symbol))

        for key, value in self.trade.notification_details().items():
            embed.add_embed_field(name=key, value=value)

        return embed

    def notify(self):
        """Send the notification."""
        webhook = DiscordWebhook(
            url=WEBHOOK_URL_TRADES,
            rate_limit_retry=True,
            username=DISCORD_USERNAME,
        )
        webhook.add_embed(self.generate_embeds())
        webhook.execute()

        return webhook


class OpenedNotification(Notification):
    """Handle opening notifications."""

    def __init__(self, trade):
        """Initialization method."""
        super().__init__(trade)


class ClosedNotification(Notification):
    """Handle closing notifications."""

    def __init__(self, trade):
        """Initialization method."""
        super().__init__(trade)


def get_handler(trade):
    """Create a trade object."""
    class_name = f"{trade.status.capitalize()}Notification"
    return globals()[class_name](trade)
