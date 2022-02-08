"""Tests for trades functions."""
import json

# import requests
from thetagang_notifications import config, trends
from thetagang_notifications.trends import Trend


def get_yf_data():
    """Read sample data from Yahoo Finance from JSON."""
    with open("tests/assets/amd_yahoo_finance.json", "r") as fileh:
        return json.load(fileh)


def load_asset(asset_filename):
    """Load an asset from test assets."""
    with open(f"tests/assets/{asset_filename}", "r") as fileh:
        return json.load(fileh)


class TestTrend:
    """Test the Trend class."""

    def test_discord_title(self):
        """Verify the discord title."""
        trendy = Trend("DOOT")
        assert trendy.discord_title == "DOOT added to trending tickers"

    def test_finviz(self, mocker):
        """Verify finviz property."""
        mocked_finviz = mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value={"Company": "Doot Industries"},
        )
        trendy = Trend("DOOT")
        assert trendy.finviz["Company"] == "Doot Industries"
        mocked_finviz.assert_called_once()
        mocked_finviz.assert_called_with("DOOT")

    def test_description_failure(self, mocker):
        """Verify description with no Finviz data."""
        mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value=None,
        )
        trendy = Trend("DOOT")
        assert trendy.discord_description == ""

    def test_description_with_earnings(self, mocker):
        """Verify description with earnings date."""
        finviz_data = {
            "Company": "DOOT Industries",
            "Sector": "Dootmaking",
            "Industry": "Heavy Doots",
            "Earnings": "Feb 29 AMC",
        }
        mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value=finviz_data,
        )
        trendy = Trend("DOOT")
        assert trendy.discord_description == (
            "DOOT Industries\nDootmaking - Heavy Doots\nEarnings: Feb 29 AMC"
        )

    def test_flush_db(self, tmpdir):
        """Verify flushing the trends database."""
        config.TRENDS_DB = str(tmpdir / "trends.db")

        trendy = Trend("DOOT")
        assert trendy.is_new is True
        trendy.save()

        Trend().flush_db()

        trendy = Trend("DOOT")
        assert trendy.is_new is True

    def test_is_new(self, tmpdir):
        """Verify that we can find new trends only."""
        config.TRENDS_DB = str(tmpdir / "trends.db")

        trendy = Trend("DOOT")
        assert trendy.is_new is True
        trendy.save()

        trendy = Trend("DOOT2")
        assert trendy.is_new is True

        trendy = Trend("DOOT")
        assert trendy.is_new is False

    def test_logo(self, mocker):
        """Verify logo property."""
        mocked_logo = mocker.patch(
            target="thetagang_notifications.utils.get_stock_logo",
            return_value="https://example.com/DOOT.png",
        )
        trendy = Trend("DOOT")
        assert trendy.logo == "https://example.com/DOOT.png"
        mocked_logo.assert_called_once()
        mocked_logo.assert_called_with("DOOT")

    def test_main_no_trends(self, mocker):
        """Test main without trends."""
        mocker.patch(
            target="thetagang_notifications.trends.download_trends",
            return_value=[],
        )
        mock_flush = mocker.patch(
            target="thetagang_notifications.trends.Trend",
            return_value=None,
        )
        trends.main()
        mock_flush.flush_db.assert_called()

    def test_main_with_trends(self, mocker):
        """Test main without trends."""
        mocker.patch(
            target="thetagang_notifications.trends.download_trends",
            return_value=["ONE", "TWO"],
        )
        mock_notify = mocker.patch(
            target="thetagang_notifications.trends.Trend.notify",
            return_value=None,
        )
        trends.main()
        mock_notify.assert_called()

    def test_notify(self, mocker):
        """Verify sending notifications."""
        finviz_data = load_asset("finviz-amd.json")
        mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value=finviz_data,
        )
        mock_exec = mocker.patch(
            target="thetagang_notifications.trends.DiscordWebhook.execute"
        )
        trendy = Trend("AMD")
        trendy.notify()

        mock_exec.assert_called_once()

        # The webhook should *not* be sent on the second run.
        mock_exec.reset_mock()
        trendy = Trend("AMD")
        trendy.notify()

        mock_exec.assert_not_called()

    def test_prepare_embed(self, mocker):
        """Verify webhook embeds."""
        mocker.patch(
            target="thetagang_notifications.utils.get_stock_logo",
            return_value="logo_url",
        )
        mocker.patch(
            target="thetagang_notifications.utils.get_stock_chart",
            return_value="chart_url",
        )
        trendy = Trend("DOOT")
        embed = trendy.prepare_embed()
        assert embed.thumbnail["url"] == "logo_url"
        assert embed.image["url"] == "chart_url"
        assert embed.title == trendy.discord_title

    def test_stock_chart(self, mocker):
        """Verify stock chart property."""
        mocked_chart = mocker.patch(
            target="thetagang_notifications.utils.get_stock_chart",
            return_value="https://example.com/DOOT.png",
        )
        trendy = Trend("DOOT")
        assert trendy.stock_chart == "https://example.com/DOOT.png"
        mocked_chart.assert_called_once()
        mocked_chart.assert_called_with("DOOT")


def test_download_trends(requests_mock):
    """Ensure we handle downloaded trends properly."""
    mocked_json = {"data": {"trends": ["DOOT"]}}
    requests_mock.get(config.TRENDS_JSON_URL, json=mocked_json)
    downloaded_trends = trends.download_trends()
    assert downloaded_trends[0] == "DOOT"
