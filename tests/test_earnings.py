"""Tests for earnings functions."""
import pytest

from thetagang_notifications import config, earnings
from thetagang_notifications.earnings import EarningsReport


# Example tweets for use with certain tests.
UNKNOWN_CONSENSUS_TWEET = "$LFVN reported earnings of $0.25 via @eWhispers"
BELOW_CONSENSUS_TWEET = (
    "$WNC reported earnings of $0.07, consensus was $0.12, Earnings Whisper was $0.16"
)
ABOVE_CONSENSUS_TWEET = (
    "$AMD reported earnings of $0.92, consensus was $0.76, Earnings Whisper was $0.81"
)
MET_CONSENSUS_TWEET = (
    "$SWK reported earnings of $2.14, consensus was $2.14, Earnings Whisper was $2.12"
)
NEGATIVE_CONSENSUS_TWEET = "$OTLK reported a loss of $0.24, consensus was ($0.33)"
JUNK_TWEET = "DOOT reported something that matches no regexes"


@pytest.mark.vcr()
def test_unknown_consensus_tweet(mocker):
    """Test an earnings report without a consensus."""
    res = EarningsReport(UNKNOWN_CONSENSUS_TWEET)
    assert res.discord_color == earnings.EARNINGS_COLOR_NO_CONSENSUS
    assert res.discord_description == (
        f"**Sector:** {res.finviz['Sector']} - {res.finviz['Industry']}\n"
        f"**Earnings:** {res.earnings} ({res.consensus})"
    )
    assert not res.consensus
    assert res.earnings == 0.25
    assert res.logo.endswith("LFVN.png")
    assert res.ticker == "LFVN"

    mock_exec = mocker.patch(
        target="thetagang_notifications.earnings.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_EARNINGS
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "LFVN: LifeVantage Corporation"
    assert embed["thumbnail"]["url"] == res.logo

    mock_exec.assert_called_once()


@pytest.mark.vcr()
def test_below_consensus_tweet(mocker):
    """Test an earnings report that missed."""
    res = EarningsReport(BELOW_CONSENSUS_TWEET)
    assert res.discord_color == earnings.EARNINGS_COLOR_MISSED
    assert res.discord_description == (
        f"**Sector:** {res.finviz['Sector']} - {res.finviz['Industry']}\n"
        f"**Earnings:** {res.earnings} ({res.consensus})"
    )
    assert res.consensus == 0.12
    assert res.earnings == 0.07
    assert res.logo.endswith(f"{res.ticker}.png")
    assert res.ticker == "WNC"

    mock_exec = mocker.patch(
        target="thetagang_notifications.earnings.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_EARNINGS
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "WNC: Wabash National Corporation"
    assert embed["thumbnail"]["url"] == res.logo

    mock_exec.assert_called_once()


@pytest.mark.vcr()
def test_above_consensus_tweet(mocker):
    """Test an earnings report that beat."""
    res = EarningsReport(ABOVE_CONSENSUS_TWEET)
    assert res.discord_color == earnings.EARNINGS_COLOR_BEAT
    assert res.discord_description == (
        f"**Sector:** {res.finviz['Sector']} - {res.finviz['Industry']}\n"
        f"**Earnings:** {res.earnings} ({res.consensus})"
    )
    assert res.consensus == 0.76
    assert res.earnings == 0.92
    assert res.logo.endswith(f"{res.ticker}.png")
    assert res.ticker == "AMD"

    mock_exec = mocker.patch(
        target="thetagang_notifications.earnings.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_EARNINGS
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "AMD: Advanced Micro Devices, Inc."
    assert embed["thumbnail"]["url"] == res.logo

    mock_exec.assert_called_once()


@pytest.mark.vcr()
def test_met_consensus_tweet(mocker):
    """Test an earnings report that met."""
    res = EarningsReport(MET_CONSENSUS_TWEET)
    assert res.discord_color == earnings.EARNINGS_COLOR_BEAT
    assert res.discord_description == (
        f"**Sector:** {res.finviz['Sector']} - {res.finviz['Industry']}\n"
        f"**Earnings:** {res.earnings} ({res.consensus})"
    )
    assert res.consensus == 2.14
    assert res.earnings == 2.14
    assert res.logo.endswith(f"{res.ticker}.png")
    assert res.ticker == "SWK"

    mock_exec = mocker.patch(
        target="thetagang_notifications.earnings.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_EARNINGS
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "SWK: Stanley Black & Decker, Inc."
    assert embed["thumbnail"]["url"] == res.logo

    mock_exec.assert_called_once()


@pytest.mark.vcr()
def test_negative_consensus_tweet(mocker):
    """Test an earnings report that met."""
    res = EarningsReport(NEGATIVE_CONSENSUS_TWEET)
    assert res.discord_color == earnings.EARNINGS_COLOR_BEAT
    assert res.discord_description == (
        f"**Sector:** {res.finviz['Sector']} - {res.finviz['Industry']}\n"
        f"**Earnings:** {res.earnings} ({res.consensus})"
    )
    assert res.consensus == -0.33
    assert res.earnings == -0.24
    assert res.logo.endswith(f"{res.ticker}.png")
    assert res.ticker == "OTLK"

    mock_exec = mocker.patch(
        target="thetagang_notifications.earnings.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_EARNINGS
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "OTLK: Outlook Therapeutics, Inc."
    assert embed["thumbnail"]["url"] == res.logo

    mock_exec.assert_called_once()


@pytest.mark.vcr()
def test_junk_tweet(mocker):
    """Test a junk tweet."""
    res = EarningsReport(JUNK_TWEET)
    mock_exec = mocker.patch(
        target="thetagang_notifications.earnings.DiscordWebhook.execute"
    )
    assert not res.consensus
    assert not res.earnings
    assert not res.finviz
    res.notify()
    mock_exec.assert_not_called()


@pytest.mark.vcr()
def test_earnings_no_finviz(mocker):
    """Test an earnings report with no finviz data."""
    mocker.patch(
        target="thetagang_notifications.utils.get_finviz_stock", return_value=None
    )
    mock_exec = mocker.patch(
        target="thetagang_notifications.earnings.DiscordWebhook.execute"
    )
    res = EarningsReport(ABOVE_CONSENSUS_TWEET)
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_EARNINGS
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "AMD"
    assert embed["thumbnail"]["url"] == res.logo

    mock_exec.assert_called_once()
