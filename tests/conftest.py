"""Pytest fixtures for the tests."""
import pytest
import requests
import vcr

REAL_TRADES = {
    "CASH_SECURED_PUT": "c90e5d5d-8158-43d7-ba09-e6a0dbbf207c",
    "COVERED_CALL": "2093163e-2d7b-424f-b007-51c46ace7bb4",
    "PUT_CREDIT_SPREAD": "7a9fe9d3-b1aa-483c-bcc0-b6f73c6b4eec",
    "SHORT_IRON_CONDOR": "8cdf95fd-d0d4-4f47-ae81-a1e000979291",
    "BUY_COMMON_STOCK": "72060eaa-7803-4124-be5b-c03b54171e75",
    "SELL_COMMON_STOCK": "a2a46a7f-1c7c-4328-98d7-32b900af98c1",
    "LONG_NAKED_PUT": "19a3beee-95e9-4c19-ab1d-712793f3eeaf",
    "SHORT_NAKED_CALL": "665b5d15-7009-49b7-8746-0e7effdf0829",
    "NON_PATRON_TRADE": "36ad8e04-b2a1-40c8-8632-55e491be10ca",
}


def real_trade_downloader(trade_title):
    """Get a real trade from thetagang.com."""
    with vcr.use_cassette(f"tests/fixtures/trades/{trade_title}.yaml"):
        url = f"https://api.thetagang.com/trades/{REAL_TRADES[trade_title]}"
        print(url)
        trade = requests.get(url).json()["data"]["trade"]

    return trade


@pytest.fixture(scope="session")
def cash_secured_put():
    """Get a cash secured put trade."""
    return real_trade_downloader("CASH_SECURED_PUT")
