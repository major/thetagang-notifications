"""Tests for thetaget functions."""
from unittest.mock import patch

import pytest

from thetagang_notifications import thetaget


@pytest.mark.vcr()
def test_get_profiles():
    """Get thetagang patreon usernames."""
    profiles = thetaget.get_profiles()

    assert type(profiles) == list
    assert 'mhayden' in profiles


@pytest.mark.vcr()
def test_get_trades_generic():
    """Get recent trades for all users."""
    resp = thetaget.get_trades()

    unique_users = set([x['User']['username'] for x in resp])

    assert type(resp) == list
    # We should have trades from multiple users.
    assert len(unique_users) > 1


@pytest.mark.vcr()
def test_get_trades_for_user():
    """Get recent trades for a user."""
    resp = thetaget.get_trades('mhayden')

    unique_users = set([x['User']['username'] for x in resp])

    assert type(resp) == list
    assert len(unique_users) == 1
    assert unique_users == set(['mhayden'])


@pytest.mark.vcr()
def test_get_single_trade():
    """Get a single trade."""
    guid = "94e5b17e-cfa4-4ab1-8b85-aff13577b1a8"
    resp = thetaget.get_single_trade(guid)

    assert type(resp) == dict
    assert resp['symbol'] == "SPY"
    assert resp['User']['username'] == 'mhayden'


@patch("thetagang_notifications.thetaget.get_trades")
@patch("thetagang_notifications.thetaget.get_profiles")
def test_get_patron_trades(profiles_fn, trades_fn):
    """Get all patron trades."""
    profiles_fn.return_value = ["user1", "user2"]
    trades_fn.return_value = ["trade1", "trade2"]

    trades = thetaget.get_patron_trades()

    assert type(trades) == list
    assert trades == ["trade1", "trade2", "trade1", "trade2"]
