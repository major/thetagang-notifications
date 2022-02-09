"""Handle earnings updates."""
import logging
import re

from discord_webhook import DiscordWebhook, DiscordEmbed
import tweepy


from thetagang_notifications import config, utils

log = logging.getLogger(__name__)


def get_consensus(tweet):
    """Get consensus for the earnings."""
    regex = r"consensus was (\(?\$[0-9\.]+\)?)"
    result = re.findall(regex, tweet)

    # Some earnings reports for smaller stocks don't have a consensus.
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


def get_earnings(tweet):
    """Get earnings or loss data."""
    # Look for positive earnings by default. 🎉
    regex = r"reported (?:earnings of )?\$([0-9\.]+)"
    multiplier = 1

    # Sometimes there's a loss and we make the number negative. 😞
    if "reported a loss of" in tweet:
        regex = r"reported a loss of \$([0-9\.]+)"
        multiplier = -1

    result = re.findall(regex, tweet)

    if result:
        return float(result[0]) * multiplier

    return None


def get_color(earnings, consensus):
    """Return a color for Discord embeds based on the earnings outcome."""
    if not consensus:
        return "000000"
    elif earnings < consensus:
        return "d42020"
    else:
        return "20d420"


def get_ticker(tweet):
    """Extract ticker from the tweet text."""
    result = re.findall(r"^\$([A-Z]+)", tweet)

    if result:
        return result[0]

    return None


def get_discord_title(data):
    """Generate a Discord title based on available data."""
    if "longName" not in data["company_details"].keys():
        return data["ticker"]

    return f"{data['ticker']}: {data['company_details']['longName']}"


def get_discord_description(data):
    """Generate a Discord description line based on earnings data."""
    details = data["company_details"]
    description_extra = "No company data found."

    if "longName" in details.keys():
        description_extra = f"**Sector:** {details['sector']} - {details['industry']}"

    description = (
        f"**Earnings:** {data['earnings']}\n"
        f"**Consensus:** {data.get('consensus', 'unknown')}\n"
    )
    return description + description_extra


def parse_earnings_tweet(tweet):
    """Parse tweet data."""
    # Parse the stock ticker.
    ticker = get_ticker(tweet)
    if not ticker:
        return None

    # Earnings or a loss?
    earnings = get_earnings(tweet)

    # Get the earnings concensus.
    consensus = get_consensus(tweet)

    # Get an emoji based on the earnings outcome.
    color = get_color(earnings, consensus)

    # Get the company name and sector/industry data.
    company_details = utils.get_symbol_details(ticker)

    return {
        "ticker": ticker,
        "earnings": earnings,
        "consensus": consensus,
        "color": color,
        "company_details": company_details,
    }


def notify_discord(earnings_data):
    """Send an earnings alert to Discord."""
    webhook = DiscordWebhook(
        url=config.WEBHOOK_URL_EARNINGS,
        username=config.DISCORD_USERNAME,
        rate_limit_retry=True,
    )
    embed = DiscordEmbed(
        title=get_discord_title(earnings_data),
        color=earnings_data["color"],
        description=get_discord_description(earnings_data),
    )

    if "longName" in earnings_data["company_details"].keys():
        embed.set_thumbnail(url=utils.get_stock_logo(earnings_data["ticker"]))
        # Temporarily disable stock charts for earnings.
        # embed.set_image(url=utils.get_stock_chart(earnings_data["ticker"]))

    webhook.add_embed(embed)
    return webhook.execute()


def handle_earnings(tweet):
    """Handle raw text from earnings tweets."""
    earnings_data = parse_earnings_tweet(tweet)

    # Unparseable tweets should just stop here.
    if earnings_data is None:
        return None

    # Let the Discord know about the results.
    notify_discord(earnings_data)

    return earnings_data


# Create a class to handle stream events.
class EarningsStream(tweepy.Stream):
    """Extending the tweepy.Stream class to do earnings things."""

    def on_connect(self):
        log.debug("Earnings: Tweepy stream connected")
        return super().on_connect()

    def on_status(self, status):
        """Parse tweets and send notifications."""
        if status.user.id == 55395551:
            log.info("Earnings: %s", status.text)
            handle_earnings(status.text)


def main():
    """Run the earnings notifications"""
    stream = EarningsStream(
        config.TWITTER_CONSUMER_KEY,
        config.TWITTER_CONSUMER_SECRET,
        config.TWITTER_ACCESS_TOKEN,
        config.TWITTER_ACCESS_TOKEN_SECRET,
    )
    stream.filter(follow=["55395551"], threaded=True)
    print("Streaming!")
