"""Test the trade queue builder."""
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from thetagang_notifications.trade_queue import (
    build_queue,
    get_trades,
    process_trade,
    trade_status,
)


@pytest.fixture
def mocked_trades():
    """Example trades for testing the queue."""
    return {
        "data": {
            "trades": [
                {
                    "guid": "1a",
                    "close_date": None,
                    "symbol": "AAPL",
                    "type": "COVERED CALL",
                    "User": {"username": "testuser", "role": "patron"},
                },
                {
                    "guid": "2b",
                    "close_date": "2020-01-01",
                    "symbol": "AAPL",
                    "type": "COVERED CALL",
                    "User": {"username": "testuser", "role": "patron"},
                },
                {
                    "guid": "3c",
                    "close_date": None,
                    "symbol": "AAPL",
                    "type": "COVERED CALL",
                    "User": {"username": "testuser", "role": "member"},
                },
                {
                    "guid": "4d",
                    "close_date": "2020-01-01",
                    "symbol": "AAPL",
                    "type": "COVERED CALL",
                    "User": {"username": "testuser", "role": "member"},
                },
            ]
        }
    }


@patch("thetagang_notifications.trade_queue.requests.get")
def test_get_trades_all(mock_requests, tmp_path, mocked_trades):
    """Get all recently updated trades."""
    fake_trades = mocked_trades.copy()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = fake_trades
    mock_requests.return_value = mock_response

    trades = get_trades()

    assert type(trades) == list
    assert len(trades) == 4


@patch("thetagang_notifications.trade_queue.requests.get")
def test_get_trades_patrons_only(mock_requests, tmp_path, mocked_trades):
    """Get all recently updated trades from patrons only."""
    fake_trades = mocked_trades.copy()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = fake_trades
    mock_requests.return_value = mock_response

    with patch("thetagang_notifications.trade_queue.PATRON_TRADES_ONLY", True):
        trades = get_trades()

    assert type(trades) == list
    assert len(trades) == 2


@patch("thetagang_notifications.trade_queue.requests.get")
def test_get_trades_skipped_users(mock_requests, tmp_path, mocked_trades):
    """Get all recently updated trades from users who aren't skipped."""
    fake_trades = mocked_trades.copy()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = fake_trades
    mock_requests.return_value = mock_response

    with patch("thetagang_notifications.trade_queue.SKIPPED_USERS", "testuser,test2"):
        trades = get_trades()

    assert type(trades) == list
    assert len(trades) == 0


@patch("redis.Redis", return_value=fakeredis.FakeStrictRedis())
@patch("thetagang_notifications.trade_queue.get_trades")
def test_build_queue(mock_get_trades, fakeredis, mocked_trades):
    """Test build_queue()."""
    fake_trades = mocked_trades["data"]["trades"].copy()
    mock_get_trades.return_value = fake_trades
    new_queue = build_queue()
    assert len(new_queue) == 4

    # If we build the queue again, it should be empty since we saw these trades already.
    new_queue = build_queue()
    assert len(new_queue) == 0


@patch("redis.Redis", return_value=fakeredis.FakeStrictRedis())
def test_process_trade_new(fakeredis, mocked_trades):
    """Test process_trade() for new trades."""
    trade = mocked_trades["data"]["trades"][0]
    assert process_trade(trade) == trade


@patch("redis.Redis", return_value=fakeredis.FakeStrictRedis())
def test_process_trade_closed(fakeredis, mocked_trades):
    """Test process_trade() for closed trades."""

    # Start with an open trade.
    trade = mocked_trades["data"]["trades"][0]
    assert process_trade(trade) == trade

    # The same open trade should not be enqueued.
    assert process_trade(trade) == []

    # Finally, the closed trade should be enqueued.
    trade["close_date"] = "2020-01-01"
    assert process_trade(trade) == trade


def test_trade_status_open():
    """Test trade_status() for open trades."""
    trade = {"close_date": None}
    assert trade_status(trade) == b"open"


def test_trade_status_closed():
    """Test trade_status() for closed trades."""
    trade = {"close_date": "2020-01-01"}
    assert trade_status(trade) == b"closed"
