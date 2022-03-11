"""Tests for trades functions."""
import pytest

from thetagang_notifications import config, trends
from thetagang_notifications.trends import Trend


@pytest.mark.vcr()
def test_download_trends():
    """Ensure we handle downloaded trends properly."""
    downloaded_trends = trends.download_trends()
    assert isinstance(downloaded_trends, list)


def test_flush_db():
    """Test flushing the database when there are no active trends."""
    res = Trend("ONE")
    assert res.is_new
    res.save()

    res = Trend("ONE")
    assert not res.is_new

    Trend.flush_db()

    res = Trend("ONE")
    assert res.is_new


@pytest.mark.vcr()
def test_trends_main(mocker):
    """Test main() in the trends module."""
    mock_trend_class = mocker.patch(target="thetagang_notifications.trends.Trend")
    trends.main()
    mock_trend_class.assert_called()


def test_trends_main_empty(mocker):
    """Test main() in the trends module when there are no trends."""
    mocker.patch(
        target="thetagang_notifications.trends.download_trends", return_value=[]
    )
    flusher = mocker.patch(target="thetagang_notifications.trends.Trend.flush_db")
    trends.main()
    flusher.assert_called_once()


@pytest.mark.vcr()
def test_trending_ticker(mocker):
    """Test handling a new trending ticker."""
    res = Trend("AMD")
    mock_exec = mocker.patch(
        target="thetagang_notifications.trends.DiscordWebhook.execute"
    )
    hook = res.notify()

    assert hook.url == config.WEBHOOK_URL_TRENDS
    assert hook.rate_limit_retry
    assert hook.username == config.DISCORD_USERNAME

    embed = hook.embeds[0]
    assert embed["title"] == "AMD added to trending tickers"
    assert embed["description"] == (
        "Advanced Micro Devices, Inc.\n"
        "Technology - Semiconductors\n"
        "Earnings: Feb 01 AMC"
    )
    assert embed["image"]["url"] == res.stock_chart
    assert embed["thumbnail"]["url"] == res.logo

    mock_exec.assert_called_once()

    # Also verify that we don't alert for the same trend twice.
    mock_exec.reset_mock()
    res.notify()
    mock_exec.assert_not_called()


@pytest.mark.vcr()
def test_trending_ticker_no_finviz(mocker):
    """Test handling a new trending ticker without finviz data."""
    res = Trend("DOOT")
    mock_exec = mocker.patch(
        target="thetagang_notifications.trends.DiscordWebhook.execute"
    )
    assert not res.discord_description
    hook = res.notify()
    assert not hook
    mock_exec.assert_not_called()
