"""Tests for trades functions."""
import json

import requests_mock

from thetagang_notifications import config, trends


def get_yf_data():
    """Read sample data from Yahoo Finance from JSON."""
    with open("tests/assets/amd_yahoo_finance.json", "r") as fileh:
        return json.load(fileh)


@requests_mock.Mocker(kw="mock")
def test_download_trends(**kwargs):
    """Ensure we handle downloaded trends properly."""
    mocked_json = {"data": {"trends": ["a trend would be here!"]}}
    kwargs["mock"].get(config.TRENDS_JSON_URL, json=mocked_json)

    downloaded_trends = trends.download_trends()
    assert downloaded_trends[0] == "a trend would be here!"


def test_diff_trends(tmp_path):
    """Verify that we can get only new trends."""
    # Prepare a temporary database.
    db_dir = tmp_path
    config.TRENDS_DB = f"{db_dir}/temp_trends.db"

    # Add some trends.
    trends.store_trends(["ONE", "TWO"])

    assert trends.diff_trends(["ONE", "TWO"]) == []

    assert trends.diff_trends(["ONE", "TWO", "THREE"]) == ["THREE"]


def test_get_previous_trends(tmp_path):
    """Verify we can get the previous trends from the database."""
    # Prepare a temporary database.
    db_dir = tmp_path
    config.TRENDS_DB = f"{db_dir}/temp_trends.db"

    # First run should come back empty.
    result = trends.get_previous_trends()
    assert result == []

    # Add some trends.
    trends.store_trends(["ONE", "TWO"])

    # We should have results now.
    result = trends.get_previous_trends()
    assert len(result) == 2
    assert result[0] == "ONE"
    assert result[1] == "TWO"


def test_notify_discord_no_details(mocker):
    """Ensure basic notifications go out when no details are available."""
    mocker.patch(
        "thetagang_notifications.utils.get_symbol_details",
        return_value={"symbol": "SPY"},
    )
    mocked_notify = mocker.patch("thetagang_notifications.trends.notify_discord_basic")
    trends.notify_discord("SPY")
    mocked_notify.assert_called_once()


def test_notify_discord_with_details(mocker):
    """Ensure fancy notifications go out when details are available."""
    stock_details = get_yf_data()
    mocker.patch(
        "thetagang_notifications.utils.get_symbol_details", return_value=stock_details
    )
    mocked_notify = mocker.patch(
        "thetagang_notifications.trends.notify_discord_fancy", return_value=None
    )
    trends.notify_discord("DOOT")
    mocked_notify.assert_called_once()


def test_notify_discord_basic(mocker):
    """Verify sending basic Discord notifications."""
    config.WEBHOOK_URL_TRENDS = "https://example_webhook_url"
    mock_discord = mocker.patch("thetagang_notifications.trends.DiscordWebhook")

    trends.notify_discord_basic({"symbol": "SPY"})
    mock_discord.assert_called_once()
    mock_discord.assert_called_once_with(
        url=config.WEBHOOK_URL_TRENDS,
        content="SPY added to trending tickers",
        rate_limit_retry=True,
        username="MajorBot 🤖",
    )
    # mock_execute.assert_called_once()


def test_notify_discord_fancy(mocker):
    """Verify sending basic Discord notifications."""
    config.WEBHOOK_URL_TRENDS = "https://example_webhook_url"
    mock_discord = mocker.patch("thetagang_notifications.trends.DiscordWebhook")

    trends.notify_discord_fancy(get_yf_data())
    mock_discord.assert_called_once()
    mock_discord.assert_called_once_with(
        url=config.WEBHOOK_URL_TRENDS, rate_limit_retry=True, username="MajorBot 🤖"
    )
    # mock_execute.assert_called_once()


def test_get_discord_description():
    """Ensure we generate a valid Discord notification description."""
    stock_details = get_yf_data()
    expected = "Advanced Micro Devices, Inc.\nTechnology - Semiconductors"
    desc = trends.get_discord_description(stock_details)
    assert desc == expected
