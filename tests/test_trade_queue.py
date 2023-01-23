"""Test the trade queue builder."""
from tempfile import mkdtemp
from unittest.mock import MagicMock, patch

from thetagang_notifications.trade_queue import (
    build_queue,
    get_trades,
    process_trade,
    trade_status,
)

MOCKED_TRADES = {
    "data": {
        "trades": [
            {"guid": "1a", "close_date": None, "User": {"role": "patron"}},
            {"guid": "2b", "close_date": "2020-01-01", "User": {"role": "patron"}},
            {"guid": "3c", "close_date": None, "User": {"role": "member"}},
            {"guid": "4d", "close_date": "2020-01-01", "User": {"role": "member"}},
        ]
    }
}


@patch("thetagang_notifications.trade_queue.STORAGE_DIR", mkdtemp())
@patch("thetagang_notifications.trade_queue.get_trades")
def test_build_queue(mock_get_trades, tmp_path):
    """Test build_queue()."""
    mock_get_trades.return_value = MOCKED_TRADES["data"]["trades"]
    new_queue = build_queue()
    assert len(new_queue) == 4

    # If we build the queue again, it should be empty since we saw these trades already.
    new_queue = build_queue()
    assert len(new_queue) == 0


@patch("thetagang_notifications.trade_queue.STORAGE_DIR", mkdtemp())
@patch("thetagang_notifications.trade_queue.requests.get")
def test_get_trades_all(mock_requests, tmp_path):
    """Get all recently updated trades."""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCKED_TRADES
    mock_requests.return_value = mock_response

    trades = get_trades()

    assert type(trades) == list
    assert len(trades) == 4


@patch("thetagang_notifications.trade_queue.STORAGE_DIR", mkdtemp())
@patch("thetagang_notifications.trade_queue.requests.get")
def test_get_trades_patrons_only(mock_requests, tmp_path):
    """Get all recently updated trades from patrons only."""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCKED_TRADES
    mock_requests.return_value = mock_response

    with patch("thetagang_notifications.trade_queue.PATRON_TRADES_ONLY", True):
        trades = get_trades()

    assert type(trades) == list
    assert len(trades) == 2


@patch("thetagang_notifications.trade_queue.STORAGE_DIR", mkdtemp())
def test_process_trade_new(tmp_path):
    """Test process_trade() for new trades."""
    trade = MOCKED_TRADES["data"]["trades"][0]
    assert process_trade(trade) == trade


@patch("thetagang_notifications.trade_queue.STORAGE_DIR", mkdtemp())
def test_process_trade_closed(tmp_path):
    """Test process_trade() for closed trades."""
    # Start with an open trade.
    trade = MOCKED_TRADES["data"]["trades"][0]
    assert process_trade(trade) == trade

    # The same open trade should not be enqueued.
    assert process_trade(trade) == []

    # Finally, the closed trade should be enqueued.
    trade["close_date"] = "2020-01-01"
    assert process_trade(trade) == trade


@patch("thetagang_notifications.trade_queue.STORAGE_DIR", mkdtemp())
def test_trade_status_open(tmp_path):
    """Test trade_status() for open trades."""
    trade = {"close_date": None}
    assert trade_status(trade) == b"open"


@patch("thetagang_notifications.trade_queue.STORAGE_DIR", mkdtemp())
def test_trade_status_closed(tmp_path):
    """Test trade_status() for closed trades."""
    trade = {"close_date": "2020-01-01"}
    assert trade_status(trade) == b"closed"
