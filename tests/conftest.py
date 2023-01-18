"""Pytest fixtures for the tests."""
import pytest
import requests
import vcr
import yaml

from thetagang_notifications.config import TRADE_SPEC_FILE


def get_trade_types():
    """Return a trade type."""
    with open(TRADE_SPEC_FILE, encoding="utf-8") as file_handle:
        spec_data = yaml.safe_load(file_handle)
    return [x["type"] for x in spec_data]


def get_example_guid(trade_type):
    """Return a GUID for a trade on thetagang.com."""
    with open(TRADE_SPEC_FILE, encoding="utf-8") as file_handle:
        spec_data = yaml.safe_load(file_handle)
    return [x["example_guid"] for x in spec_data if x["type"] == trade_type][0]


@pytest.fixture(scope="session", params=get_trade_types())
def real_trades(request):
    """Get a real trade from thetagang.com."""
    example_guid = get_example_guid(request.param)
    cassette = f"tests/fixtures/trades/{request.param.replace(' ', '_')}.yaml"

    with vcr.use_cassette(cassette):
        url = f"https://api.thetagang.com/trades/{example_guid}"
        trade = requests.get(url).json()["data"]["trade"]

    return trade
