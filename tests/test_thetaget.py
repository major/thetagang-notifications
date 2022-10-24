"""Tests for thetaget functions."""
import os
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from thetagang_notifications import thetaget


@freeze_time("2022-09-29")
def test_day_diff():
    """Test the subtraction of dates."""
    days = thetaget.day_diff("2022-09-27T00:00:00.000Z")
    assert days == 2


@freeze_time("2022-09-29")
def test_filter_recent():
    """Ensure trades are filtered for recent dates."""
    trades = [
        {"updatedAt": "2022-09-27T00:00:00.000Z"},
        {"updatedAt": "2022-09-01T00:00:00.000Z"},
    ]
    valid_trades = thetaget.filter_recent(trades)

    assert valid_trades == [{"updatedAt": "2022-09-27T00:00:00.000Z"}]


@pytest.mark.vcr()
def test_get_profiles():
    """Get thetagang patreon usernames."""
    profiles = thetaget.get_profiles()

    assert type(profiles) == list
    assert "mhayden" in profiles


@pytest.mark.vcr()
def test_get_trades_generic():
    """Get recent trades for all users."""
    resp = thetaget.get_trades()

    unique_users = {x["User"]["username"] for x in resp}

    assert type(resp) == list
    # We should have trades from multiple users.
    assert len(unique_users) > 1


@pytest.mark.vcr()
def test_get_trades_for_user():
    """Get recent trades for a user."""
    resp = thetaget.get_trades("mhayden")

    unique_users = {x["User"]["username"] for x in resp}

    assert type(resp) == list
    assert len(unique_users) == 1
    assert unique_users == {"mhayden"}


@pytest.mark.vcr()
def test_get_single_trade():
    """Get a single trade."""
    guid = "94e5b17e-cfa4-4ab1-8b85-aff13577b1a8"
    resp = thetaget.get_single_trade(guid)

    assert type(resp) == dict
    assert resp["symbol"] == "SPY"
    assert resp["User"]["username"] == "mhayden"


@freeze_time("2022-09-29")
@patch("thetagang_notifications.thetaget.get_trades")
@patch("thetagang_notifications.thetaget.get_profiles")
def test_get_patron_trades(profiles_fn, trades_fn):
    """Get all patron trades."""
    profiles_fn.return_value = ["user1", "user2"]
    trades_fn.return_value = [
        {"updatedAt": "2022-09-27T00:00:00.000Z"},
        {"updatedAt": "2022-09-01T00:00:00.000Z"},
    ]

    trades = thetaget.get_patron_trades()

    assert type(trades) == list
    assert trades == [
        {"updatedAt": "2022-09-27T00:00:00.000Z"},
        {"updatedAt": "2022-09-27T00:00:00.000Z"},
    ]


@pytest.mark.vcr()
def test_get_trade_screenshot():
    """Get a trade's screenshot."""
    guid = "a8914cb0-3973-4037-967c-8196abce2042"
    res = thetaget.get_trade_screenshot(guid)

    assert res.endswith(f"{guid}.png")
    assert os.path.isfile(res)
