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


def get_earnings_phrase(earnings, consensus):
    """Return a phrase based on results."""
    if not consensus:
        return "reported without analyst consensus"
    elif earnings == consensus:
        return "met expectations"
    elif earnings < consensus:
        return "missed expectations"
    else:
        return "beat expectations"


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


def get_discord_description(data):
    """Generate a Discord description line based on earnings data."""
    details = data["company_details"]
    description = "No company details found."

    if "Company" in details.keys():
        description = (
            f"{details['Industry']} ({details['Sector']} - {details['Industry']})"
        )

    return description


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

    # Get the earnings phrase missed/beat/met.
    phrase = get_earnings_phrase(earnings, consensus)

    # Get the company name and sector/industry data from Finviz
    company_details = utils.get_symbol_details(ticker)

    return {
        "ticker": ticker,
        "earnings": earnings,
        "consensus": consensus,
        "color": color,
        "phrase": phrase,
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
        title=f"{earnings_data['ticker']} {earnings_data['phrase']}",
        color=earnings_data["color"],
        description=get_discord_description(earnings_data),
    )
    embed.set_thumbnail(url=utils.get_stock_logo(earnings_data["ticker"]))
    embed.add_embed_field(name="Earnings", value=f"{earnings_data['earnings']}")
    embed.add_embed_field(name="Consensus", value=f"{earnings_data['consensus']}")
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
    stream.filter(track=["AMD"], threaded=True)
    # stream.filter(follow=["55395551"])
    print("Streaming!")
