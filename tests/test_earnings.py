"""Tests for earnings functions."""
import json

from thetagang_notifications import config, earnings


# Example tweets for use with certain tests.
UNKNOWN_CONSENSUS_TWEET = "$LFVN reported earnings of $0.25 via @eWhispers"
BELOW_CONSENSUS_TWEET = (
    "$WNC reported earnings of $0.07, consensus was $0.12, Earnings Whisper was $0.16"
)
ABOVE_CONSENSUS_TWEET = (
    "$AMD reported earnings of $0.92, consensus was $0.76, Earnings Whisper was $0.81"
)
MET_CONSENSUS_TWEET = (
    "$SWK reported earnings of $2.14, consensus was $2.06, Earnings Whisper was $2.12"
)
NEGATIVE_CONSENSUS_TWEET = "$OTLK reported a loss of $0.24, consensus was ($0.33)"
JUNK_TWEET = "DOOT reported something that matches no regexes"


def get_yf_data():
    """Read sample data from Yahoo Finance from JSON."""
    with open("tests/assets/amd_yahoo_finance.json", "r") as fileh:
        return json.load(fileh)


def test_get_consensus():
    """Ensure we get the consensus from the earnings tweet properly."""
    consensus = earnings.get_consensus(UNKNOWN_CONSENSUS_TWEET)
    assert consensus is None

    consensus = earnings.get_consensus(BELOW_CONSENSUS_TWEET)
    assert consensus == 0.12

    consensus = earnings.get_consensus(NEGATIVE_CONSENSUS_TWEET)
    assert consensus == -0.33


def test_get_earnings():
    """Ensure we get the earnings number from the earnings tweet properly."""
    earned = earnings.get_earnings(UNKNOWN_CONSENSUS_TWEET)
    assert earned == 0.25

    earned = earnings.get_earnings(NEGATIVE_CONSENSUS_TWEET)
    assert earned == -0.24

    earned = earnings.get_earnings(JUNK_TWEET)
    assert earned is None


def test_get_color():
    """Verify that we return the right color based on earnings/consensus."""
    emoji = earnings.get_color(0.50, 0.25)
    assert emoji == "20d420"

    emoji = earnings.get_color(0.25, 0.50)
    assert emoji == "d42020"

    emoji = earnings.get_color(0.25, None)
    assert emoji == "000000"


def test_get_ticker():
    """Ensure we can extract the stock ticker if it is present."""
    ticker = earnings.get_ticker(BELOW_CONSENSUS_TWEET)
    assert ticker == "WNC"

    ticker = earnings.get_ticker(JUNK_TWEET)
    assert ticker is None


def test_parse_earnings_tweet_without_ticker(mocker):
    """Verify we abort early if the tweet has no ticker in it."""
    result = earnings.parse_earnings_tweet(JUNK_TWEET)
    assert result is None


def test_parse_earnings_tweet_unknown_consensus(mocker):
    """Verify handling of tweets with an unknown concensus."""
    expected_result = {
        "company_details": {"symbol": "DOOT"},
        "consensus": None,
        "earnings": 0.25,
        "color": "000000",
        "ticker": "LFVN",
    }
    mocker.patch(
        "thetagang_notifications.utils.get_symbol_details",
        return_value=expected_result["company_details"],
    )
    result = earnings.parse_earnings_tweet(UNKNOWN_CONSENSUS_TWEET)
    assert result == expected_result


def test_parse_earnings_tweet_negative_consensus(mocker):
    """Verify handling of tweets with a negative consensus and earnings."""
    expected_result = {
        "company_details": {"symbol": "DOOT"},
        "consensus": -0.33,
        "earnings": -0.24,
        "color": "20d420",
        "ticker": "OTLK",
    }
    mocker.patch(
        "thetagang_notifications.utils.get_symbol_details",
        return_value=expected_result["company_details"],
    )
    result = earnings.parse_earnings_tweet(NEGATIVE_CONSENSUS_TWEET)
    assert result == expected_result


def test_parse_earnings_tweet_met_consensus(mocker):
    """Verify handling of tweets with earnings at consensus."""
    expected_result = {
        "company_details": {"symbol": "DOOT"},
        "consensus": 2.06,
        "earnings": 2.14,
        "color": "20d420",
        "ticker": "SWK",
    }
    mocker.patch(
        "thetagang_notifications.utils.get_symbol_details",
        return_value=expected_result["company_details"],
    )
    result = earnings.parse_earnings_tweet(MET_CONSENSUS_TWEET)
    assert result == expected_result


def test_parse_earnings_tweet_above_consensus(mocker):
    """Verify handling of tweets with earnings above consensus."""
    expected_result = {
        "company_details": {"symbol": "DOOT"},
        "consensus": 0.76,
        "earnings": 0.92,
        "color": "20d420",
        "ticker": "AMD",
    }
    mocker.patch(
        "thetagang_notifications.utils.get_symbol_details",
        return_value=expected_result["company_details"],
    )
    result = earnings.parse_earnings_tweet(ABOVE_CONSENSUS_TWEET)
    assert result == expected_result


def test_parse_earnings_tweet_below_consensus(mocker):
    """Verify handling of tweets with earnings below consensus."""
    expected_result = {
        "company_details": {"symbol": "DOOT"},
        "consensus": 0.12,
        "earnings": 0.07,
        "color": "d42020",
        "ticker": "WNC",
    }
    mocker.patch(
        "thetagang_notifications.utils.get_symbol_details",
        return_value=expected_result["company_details"],
    )
    result = earnings.parse_earnings_tweet(BELOW_CONSENSUS_TWEET)
    assert result == expected_result


def test_get_discord_title_no_data():
    """Ensure we generate a discord title without company data."""
    earnings_data = {
        "company_details": {"symbol": "DOOT"},
        "consensus": 0.12,
        "earnings": 0.07,
        "color": "d42020",
        "ticker": "DOOT",
    }
    expected = "**Earnings:** 0.07\n**Consensus:** 0.12\nNo company data found."
    desc = earnings.get_discord_description(earnings_data)
    assert desc == expected


def test_get_discord_title_with_data():
    """Ensure we generate a discord title with company data."""
    stock_details = get_yf_data()
    earnings_data = {
        "company_details": stock_details,
        "consensus": 0.12,
        "earnings": 0.07,
        "color": "d42020",
        "ticker": "DOOT",
    }
    expected_desc = (
        "**Earnings:** 0.07\n"
        "**Consensus:** 0.12\n"
        "**Sector:** Technology - Semiconductors"
    )
    desc = earnings.get_discord_description(earnings_data)
    assert desc == expected_desc


def test_get_discord_description_no_data():
    """Ensure we generate a discord description without company data."""
    earnings_data = {
        "company_details": {"symbol": "DOOT"},
        "consensus": 0.12,
        "earnings": 0.07,
        "color": "d42020",
        "ticker": "DOOT",
    }
    expected = "**Earnings:** 0.07\n**Consensus:** 0.12\nNo company data found."
    desc = earnings.get_discord_description(earnings_data)
    assert desc == expected


def test_get_discord_description_with_data():
    """Ensure we generate a discord description with company data."""
    stock_details = get_yf_data()
    earnings_data = {
        "company_details": stock_details,
        "consensus": 0.12,
        "earnings": 0.07,
        "color": "d42020",
        "ticker": "DOOT",
    }
    expected_desc = (
        "**Earnings:** 0.07\n"
        "**Consensus:** 0.12\n"
        "**Sector:** Technology - Semiconductors"
    )
    desc = earnings.get_discord_description(earnings_data)
    assert desc == expected_desc


def test_notify_discord_no_data(mocker):
    """Verify sending basic Discord notifications without stock data."""
    earnings_data = {
        "company_details": {"symbol": "DOOT"},
        "consensus": 0.12,
        "earnings": 0.07,
        "color": "d42020",
        "ticker": "DOOT",
    }
    config.WEBHOOK_URL_EARNINGS = "https://example_webhook_url"
    mock_discord = mocker.patch("thetagang_notifications.earnings.DiscordWebhook")

    earnings.notify_discord(earnings_data)
    mock_discord.assert_called_once()
    mock_discord.assert_called_once_with(
        url=config.WEBHOOK_URL_EARNINGS, rate_limit_retry=True, username="MajorBot 🤖"
    )


def test_notify_discord(mocker):
    """Verify sending basic Discord notifications."""
    stock_details = get_yf_data()
    earnings_data = {
        "company_details": stock_details,
        "consensus": 0.12,
        "earnings": 0.07,
        "color": "d42020",
        "ticker": "DOOT",
    }
    config.WEBHOOK_URL_EARNINGS = "https://example_webhook_url"
    mock_discord = mocker.patch("thetagang_notifications.earnings.DiscordWebhook")

    earnings.notify_discord(earnings_data)
    mock_discord.assert_called_once()
    mock_discord.assert_called_once_with(
        url=config.WEBHOOK_URL_EARNINGS, rate_limit_retry=True, username="MajorBot 🤖"
    )


def test_handle_earnings_bad_tweet(mocker):
    """Verify that we handle bad tweets handed off from Tweepy."""
    mocker.patch("thetagang_notifications.earnings.notify_discord")

    result = earnings.handle_earnings("junk tweet")
    assert result is None


def test_handle_earnings_good_tweet(mocker):
    """Verify that we handle earnings tweets handed off from Tweepy."""
    mocked_notify = mocker.patch("thetagang_notifications.earnings.notify_discord")
    mocker.patch("thetagang_notifications.utils.get_symbol_details")

    result = earnings.handle_earnings(BELOW_CONSENSUS_TWEET)
    assert result["ticker"] == "WNC"
    mocked_notify.assert_called_once()
