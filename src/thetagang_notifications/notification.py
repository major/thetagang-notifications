"""Send notifications to discord for trades."""

from typing import TYPE_CHECKING, Any

from discord_webhook import DiscordEmbed, DiscordWebhook

if TYPE_CHECKING:
    from thetagang_notifications.trade import Trade

from thetagang_notifications.config import settings

STOCK_LOGO = "https://static.stocktitan.net/company-logo/%s.webp"


class Notification:
    """Base class for discord notifications."""

    def __init__(self, trade: "Trade") -> None:
        """Initialization method."""
        self.trade = trade
        self.trade_note = self.trade.note if self.trade.is_open else self.trade.closing_note

        # Choose an action icon based on the trade status.
        self.icon_url = settings.opening_trade_icon if self.trade.is_open else settings.closing_trade_icon

    def generate_action(self) -> dict:
        """Generate the action for the notification."""
        return {
            "name": f"{self.trade.username} {self.trade.status} a trade",
            "icon_url": self.trade.avatar if self.trade.avatar else self.icon_url,
            "url": f"https://thetagang.com/{self.trade.username}/{self.trade.guid}",
        }

    def generate_embeds(self) -> DiscordEmbed:
        """Generate the embeds for the notification."""
        embed = DiscordEmbed(
            title=self.trade.notification_title(),
            description=self.trade.opening_description(),
        )

        embed.set_author(**self.generate_action())
        embed.set_image(url=settings.transparent_png)
        embed.set_thumbnail(url=STOCK_LOGO % self.trade.symbol.lower())
        embed.set_footer(text=self.trade_note)

        return embed

    def notify(self) -> DiscordWebhook:
        """Send the notification."""
        webhook = DiscordWebhook(
            url=settings.webhook_url_trades,
            rate_limit_retry=True,
            username=settings.discord_username,
        )
        webhook.add_embed(self.generate_embeds())
        webhook.execute()

        return webhook


class OpenedNotification(Notification):
    """Handle opening notifications."""

    def __init__(self, trade: "Trade"):
        """Initialization method."""
        super().__init__(trade)


class ClosedNotification(Notification):
    """Handle closing notifications."""

    def __init__(self, trade: "Trade"):
        """Initialization method."""
        super().__init__(trade)
        self.trade_color = (
            settings.color_assigned if self.trade.is_assigned else settings.color_winner if self.trade.is_winner else settings.color_loser
        )

    def generate_embeds(self) -> DiscordEmbed:
        """Generate the embeds for the notification."""
        embed = DiscordEmbed(
            title=self.trade.closing_description(),
            description=self.trade.notification_title(),
            color=self.trade_color,
        )
        embed.set_author(**self.generate_action())
        embed.set_image(url=settings.transparent_png)
        embed.set_thumbnail(url=STOCK_LOGO % self.trade.symbol.lower())
        embed.set_footer(text=self.trade_note)

        return embed


def get_notifier(trade: Any) -> Notification:
    """Create a trade object."""
    available_notifications = {
        "opened": OpenedNotification,
        "closed": ClosedNotification,
    }
    return available_notifications[trade.status](trade)
