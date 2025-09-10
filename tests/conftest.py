"""Pytest fixtures for the tests."""

import httpx
import pytest
import vcr
from ruyaml import YAML

from thetagang_notifications.config import settings


def get_trade_types():
    """Return a trade type."""
    yaml = YAML(typ='safe', pure=True)
    with open(settings.trade_spec_file, encoding="utf-8") as file_handle:
        spec_data = yaml.load(file_handle)
    return [x["type"] for x in spec_data]


def get_example_guid(trade_type):
    """Return a GUID for a trade on thetagang.com."""
    yaml = YAML(typ='safe', pure=True)
    with open(settings.trade_spec_file, encoding="utf-8") as file_handle:
        spec_data = yaml.load(file_handle)
    return next(x["example_guid"] for x in spec_data if x["type"] == trade_type)


@pytest.fixture(scope="session", params=get_trade_types())
def real_trades(request):
    """Get a real trade from thetagang.com."""
    example_guid = get_example_guid(request.param)
    cassette = f"tests/fixtures/trades/{request.param.replace(' ', '_')}.yaml"

    with vcr.use_cassette(cassette):
        url = f"https://api3.thetagang.com/trades/{example_guid}"
        trade = httpx.get(url, timeout=15).json()["data"]

    return trade
