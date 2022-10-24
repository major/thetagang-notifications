"""Handle earnings updates."""
import logging
import re
from functools import cached_property

import tweepy
from discord_webhook import DiscordEmbed, DiscordWebhook

from thetagang_notifications import config, utils

log = logging.getLogger(__name__)

# Earnings notification colors.
EARNINGS_COLOR_BEAT = "20d420"
EARNINGS_COLOR_MISSED = "d42020"
EARNINGS_COLOR_NO_CONSENSUS = "000000"

# Wide, transparent PNG that helps to keep the earnings embeds the same width.
TRANSPARENT_PNG = "https://cdn.major.io/wide-empty-transparent.png"


class EarningsReport:
    """Class for handling new earnings reports."""

    def __init__(self, tweet):
        """Initialize the basics of the class."""
        self.tweet = tweet

    @property
    def consensus(self):
        """Find the consensus rating in the tweet (if present)."""
        regex = r"consensus was (\(?\$[0-9\.]+\)?)"
        result = re.findall(regex, self.tweet)

        # Some earnings reports, especially for smaller stocks, don't have an analyst
        # consensus number.
        if not result:
            return None

        # Parse the consensus and handle negative numbers.
        raw_consensus = result[0]
        if "(" in raw_consensus:
            # We have an expected loss.
            consensus = float(re.findall(r"[0-9\.]+", raw_consensus)[0]) * -1
        else:
            # We have an expected gain.
            consensus = float(re.findall(r"[0-9\.]+", raw_consensus)[0])

        return consensus

    @property
    def discord_color(self):
        """Choose a color based on the consensus and earnings relationship."""
        if not self.consensus:
            return EARNINGS_COLOR_NO_CONSENSUS
        elif self.earnings < self.consensus:
            return EARNINGS_COLOR_MISSED
        else:
            return EARNINGS_COLOR_BEAT

    @property
    def discord_description(self):
        """Generate a description for the Discord notification."""
        description = [f"**Earnings:** {self.earnings} ({self.consensus})"]

        if self.finviz:
            description = [
                f"**Sector:** {self.finviz['Sector']} - {self.finviz['Industry']}"
            ] + description

        return "\n".join(description)

    @property
    def earnings(self):
        """Find the earnings number in the tweet."""
        # Look for positive earnings by default. 🎉
        regex = r"reported (?:earnings of )?\$([0-9\.]+)"
        multiplier = 1

        # Sometimes there's a loss and we make the number negative. 😞
        if "reported a loss of" in self.tweet:
            regex = r"reported a loss of \$([0-9\.]+)"
            multiplier = -1

        # Search for earnings results and exit early if they are missing.
        result = re.findall(regex, self.tweet)
        if not result:
            return None

        return float(result[0]) * multiplier

    @cached_property
    def finviz(self):
        """Get data from finviz.com about our trending symbol."""
        return utils.get_finviz_stock(self.ticker)

    @property
    def logo(self):
        """Get the stock logo."""
        return utils.get_stock_logo(self.ticker)

    @property
    def discord_title(self):
        """Generate a title for the notification."""
        if self.finviz:
            return f"{self.ticker}: {self.finviz['Company']}"

        return self.ticker

    def notify(self):
        """Send notification to Discord."""
        # Exit early if we couldn't find a ticker in the tweet.
        if not self.ticker:
            return None

        webhook = DiscordWebhook(
            url=config.WEBHOOK_URL_EARNINGS,
            rate_limit_retry=True,
            username=config.DISCORD_USERNAME,
        )
        webhook.add_embed(self.prepare_embed())
        webhook.execute()
        return webhook

    def prepare_embed(self):
        """Prepare the webhook embed data."""
        embed = DiscordEmbed(
            title=self.discord_title,
            color=self.discord_color,
            description=self.discord_description,
        )
        embed.set_thumbnail(url=self.logo)
        # Temporarily disable the transparent image to make the embed less tall.
        # embed.set_image(url=TRANSPARENT_PNG)
        return embed

    @property
    def ticker(self):
        """Find the ticker in the earnings tweet."""
        result = re.findall(r"^\$([A-Z]+)", self.tweet)
        return result[0] if result else None


# Create a class to handle stream events.
class EarningsStream(tweepy.Stream):  # pragma: no cover
    """Extending the tweepy.Stream class to do earnings things."""

    def on_connect(self):
        log.debug("Earnings: Tweepy stream connected")
        return super().on_connect()

    def on_status(self, status):
        """Parse tweets and send notifications."""
        if status.user.id == 55395551:
            log.info("Earnings: %s", status.text)
            ern = EarningsReport(status.text)
            ern.notify()


def main():  # pragma: no cover
    """Run the earnings notifications."""
    stream = EarningsStream(
        config.TWITTER_CONSUMER_KEY,
        config.TWITTER_CONSUMER_SECRET,
        config.TWITTER_ACCESS_TOKEN,
        config.TWITTER_ACCESS_TOKEN_SECRET,
    )
    stream.filter(follow=["55395551"], threaded=True)
    print("Streaming!")


if __name__ == "__main__":  # pragma: no cover
    main()
