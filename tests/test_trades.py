"""Tests for trades functions."""
import requests_mock


from thetagang_notifications import config, trades


@requests_mock.Mocker(kw="mock")
def test_download_trades(**kwargs):
    """Ensure we handle downloaded trades properly."""
    mocked_json = {"data": {"trades": ["a trade would be here!"]}}
    kwargs["mock"].get(config.TRADES_JSON_URL, json=mocked_json)

    downloaded_trades = trades.download_trades()
    assert downloaded_trades[0] == "a trade would be here!"
