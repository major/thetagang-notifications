"""Tests for earnings functions."""
import json

from thetagang_notifications import earnings
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
    "$SWK reported earnings of $2.14, consensus was $2.06, Earnings Whisper was $2.12"
)
NEGATIVE_CONSENSUS_TWEET = "$OTLK reported a loss of $0.24, consensus was ($0.33)"
JUNK_TWEET = "DOOT reported something that matches no regexes"


def get_yf_data():
    """Read sample data from Yahoo Finance from JSON."""
    with open("tests/assets/amd_yahoo_finance.json", "r") as fileh:
        return json.load(fileh)


def load_asset(asset_filename):
    """Load an asset from test assets."""
    with open(f"tests/assets/{asset_filename}", "r") as fileh:
        return json.load(fileh)


class TestEarnings:
    """Tests for the EarningsReport class."""

    def test_consensus(self):
        """Test consensus extraction."""
        res = EarningsReport(UNKNOWN_CONSENSUS_TWEET)
        assert not res.consensus

        res = EarningsReport(BELOW_CONSENSUS_TWEET)
        assert res.consensus == 0.12

        res = EarningsReport(NEGATIVE_CONSENSUS_TWEET)
        assert res.consensus == -0.33

    def test_earnings(self):
        """Test consensus extraction."""
        res = EarningsReport(JUNK_TWEET)
        assert not res.earnings

        res = EarningsReport(BELOW_CONSENSUS_TWEET)
        assert res.earnings == 0.07

        res = EarningsReport(NEGATIVE_CONSENSUS_TWEET)
        assert res.earnings == -0.24

    def test_finviz(self, mocker):
        """Verify finviz property."""
        mocked_finviz = mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value={"Company": "Doot Industries"},
        )
        res = EarningsReport("$DOOT reported a loss of $0.69, consensus was ($1.69)")
        assert res.finviz["Company"] == "Doot Industries"
        mocked_finviz.assert_called_once()
        mocked_finviz.assert_called_with("DOOT")

    def test_ticker(self):
        """Test ticker extraction."""
        res = EarningsReport(JUNK_TWEET)
        assert not res.ticker

        res = EarningsReport(ABOVE_CONSENSUS_TWEET)
        assert res.ticker == "AMD"

    def test_logo(self, mocker):
        """Verify logo property."""
        mocked_logo = mocker.patch(
            target="thetagang_notifications.utils.get_stock_logo",
            return_value="https://example.com/AMD.png",
        )
        res = EarningsReport(ABOVE_CONSENSUS_TWEET)
        assert res.logo == "https://example.com/AMD.png"
        mocked_logo.assert_called_once()
        mocked_logo.assert_called_with("AMD")

    def test_notificiation_color(self):
        """Test notification colors."""
        res = EarningsReport(JUNK_TWEET)
        assert res.discord_color == earnings.EARNINGS_COLOR_NO_CONSENSUS

        res = EarningsReport(BELOW_CONSENSUS_TWEET)
        assert res.discord_color == earnings.EARNINGS_COLOR_MISSED

        res = EarningsReport(ABOVE_CONSENSUS_TWEET)
        assert res.discord_color == earnings.EARNINGS_COLOR_BEAT

        res = EarningsReport(MET_CONSENSUS_TWEET)
        assert res.discord_color == earnings.EARNINGS_COLOR_BEAT

        res = EarningsReport(NEGATIVE_CONSENSUS_TWEET)
        assert res.discord_color == earnings.EARNINGS_COLOR_BEAT

        res = EarningsReport(JUNK_TWEET)
        assert res.discord_color == earnings.EARNINGS_COLOR_NO_CONSENSUS

    def test_notification_description(self, mocker):
        """Verify notification description."""
        mocked_finviz = mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value=load_asset("finviz-amd.json"),
        )
        res = EarningsReport(ABOVE_CONSENSUS_TWEET)
        assert res.discord_description == "\n".join(
            [
                "**Sector:** Technology - Semiconductors",
                "**Earnings:** 0.92",
                "**Consensus:** 0.76",
            ]
        )

        mocked_finviz.assert_called_once()

    def test_notification_description_no_finviz(self, mocker):
        """Verify notification description when finviz has no data."""
        mocked_finviz = mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock", return_value=None
        )
        res = EarningsReport(ABOVE_CONSENSUS_TWEET)
        assert res.discord_description == "\n".join(
            [
                "**Earnings:** 0.92",
                "**Consensus:** 0.76",
            ]
        )

        mocked_finviz.assert_called_once()

    def test_discord_title(self, mocker):
        """Verify notification titles."""
        mocked_finviz = mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value=load_asset("finviz-amd.json"),
        )
        res = EarningsReport(ABOVE_CONSENSUS_TWEET)
        assert res.discord_title == "AMD: Advanced Micro Devices, Inc."

        mocked_finviz.assert_called_once()

    def test_discord_title_no_data(self, mocker):
        """Verify notification when there is no finviz data."""
        mocked_finviz = mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value=None,
        )
        res = EarningsReport(ABOVE_CONSENSUS_TWEET)
        assert res.discord_title == "AMD"

        mocked_finviz.assert_called_once()

    def test_notify(self, mocker):
        """Verify sending notifications."""
        mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value=load_asset("finviz-amd.json"),
        )
        mock_exec = mocker.patch(
            target="thetagang_notifications.earnings.DiscordWebhook.execute"
        )
        res = EarningsReport(ABOVE_CONSENSUS_TWEET)
        res.notify()
        mock_exec.assert_called_once()

    def test_notify_missing_ticker(self, mocker):
        """Verify sending notifications with a missing ticker."""
        mock_exec = mocker.patch(
            target="thetagang_notifications.earnings.DiscordWebhook.execute"
        )
        res = EarningsReport(JUNK_TWEET)
        result = res.notify()

        assert not result
        mock_exec.assert_not_called()

    def test_prepare_embed(self, mocker):
        """Verify webhook embeds."""
        mocker.patch(
            target="thetagang_notifications.utils.get_finviz_stock",
            return_value=load_asset("finviz-amd.json"),
        )
        mocker.patch(
            target="thetagang_notifications.utils.get_stock_logo",
            return_value="logo_url",
        )
        res = EarningsReport(ABOVE_CONSENSUS_TWEET)
        embed = res.prepare_embed()
        assert embed.thumbnail["url"] == "logo_url"
        assert embed.image["url"] == earnings.TRANSPARENT_PNG
        assert embed.title == res.discord_title
        assert embed.description == res.discord_description
