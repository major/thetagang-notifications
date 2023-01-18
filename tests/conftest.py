"""Pytest fixtures for the tests."""
import pytest
import requests
import vcr

# List of trades on thetagang.com to use as data for tests.
REAL_TRADES = {
    "CASH SECURED PUT": "c90e5d5d-8158-43d7-ba09-e6a0dbbf207c",
    "COVERED CALL": "2093163e-2d7b-424f-b007-51c46ace7bb4",
    "PUT CREDIT SPREAD": "7a9fe9d3-b1aa-483c-bcc0-b6f73c6b4eec",
    "SHORT IRON CONDOR": "8cdf95fd-d0d4-4f47-ae81-a1e000979291",
    "BUY COMMON STOCK": "72060eaa-7803-4124-be5b-c03b54171e75",
    "SELL COMMON STOCK": "a2a46a7f-1c7c-4328-98d7-32b900af98c1",
    "LONG NAKED PUT": "19a3beee-95e9-4c19-ab1d-712793f3eeaf",
    "SHORT NAKED CALL": "665b5d15-7009-49b7-8746-0e7effdf0829",
}


@pytest.fixture(scope="session")
def real_trade(request):
    """Get a real trade from thetagang.com."""
    if request.param not in REAL_TRADES:
        raise ValueError(f"No real trade guid fixture for `{request.param}`.")

    with vcr.use_cassette(f"tests/fixtures/trades/{request.param}.yaml"):
        url = f"https://api.thetagang.com/trades/{REAL_TRADES[request.param]}"
        trade = requests.get(url).json()["data"]["trade"]

    return trade
