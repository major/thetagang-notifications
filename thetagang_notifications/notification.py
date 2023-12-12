"""Send notifications to discord for trades."""

from discord_webhook import DiscordEmbed, DiscordWebhook

from thetagang_notifications.config import (
    CLOSING_TRADE_ICON,
    COLOR_ASSIGNED,
    COLOR_LOSER,
    COLOR_WINNER,
    DISCORD_USERNAME,
    OPENING_TRADE_ICON,
    TRANSPARENT_PNG,
    WEBHOOK_URL_TRADES,
)

STOCK_LOGO = "https://s3.amazonaws.com/logos.atom.finance/stocks-and-funds/%s.png"


class Notification:
    """Base class for discord notifications."""

    def __init__(self, trade):
        """Initialization method."""
        self.trade = trade
        self.trade_note = self.trade.note if self.trade.is_open else self.trade.closing_note

        # Choose an action icon based on the trade status.
        self.icon_url = OPENING_TRADE_ICON if self.trade.is_open else CLOSING_TRADE_ICON

    def generate_action(self):
        """Generate the action for the notification."""
        return {
            "name": f"{self.trade.username} {self.trade.status} a trade",
            "icon_url": self.icon_url,
            "url": f"https://thetagang.com/{self.trade.username}/{self.trade.guid}",
        }

    def generate_embeds(self):
        """Generate the embeds for the notification."""
        embed = DiscordEmbed(
            title=self.trade.notification_title(),
            description=self.trade.opening_description(),
        )

        embed.set_author(**self.generate_action())
        embed.set_image(url=TRANSPARENT_PNG)
        embed.set_thumbnail(url=STOCK_LOGO % self.trade.symbol)
        embed.set_footer(text=self.trade_note)

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
        self.trade_color = (
            COLOR_ASSIGNED if self.trade.is_assigned else COLOR_WINNER if self.trade.is_winner else COLOR_LOSER
        )

    def generate_embeds(self):
        """Generate the embeds for the notification."""
        embed = DiscordEmbed(
            title=self.trade.closing_description(),
            description=self.trade.notification_title(),
            color=self.trade_color,
        )
        embed.set_author(**self.generate_action())
        embed.set_image(url=TRANSPARENT_PNG)
        embed.set_thumbnail(url=STOCK_LOGO % self.trade.symbol)
        embed.set_footer(text=self.trade_note)

        return embed


def get_notifier(trade):
    """Create a trade object."""
    available_notifications = {
        "opened": OpenedNotification,
        "closed": ClosedNotification,
    }
    return available_notifications[trade.status](trade)
