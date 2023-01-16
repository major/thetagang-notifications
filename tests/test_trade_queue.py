"""Test the trade queue builder."""
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
            {"guid": "1a", "close_date": None},
            {"guid": "2b", "close_date": "2020-01-01"},
        ]
    }
}


@patch("thetagang_notifications.trade_queue.get_trades")
def test_build_queue(mock_get_trades):
    """Test build_queue()."""
    mock_get_trades.return_value = MOCKED_TRADES["data"]["trades"]
    new_queue = build_queue()
    assert len(new_queue) == 2

    # If we build the queue again, it should be empty since we saw these trades already.
    new_queue = build_queue()
    assert len(new_queue) == 0


@patch("thetagang_notifications.trade_queue.requests.get")
def test_get_trades(mock_requests):
    """Get all recently updated trades."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCKED_TRADES
    mock_requests.return_value = mock_response

    trades = get_trades()

    assert type(trades) == list
    assert trades[0]["close_date"] == "2020-01-01"
    assert trades[1]["close_date"] is None


def test_process_trade_new():
    """Test process_trade() for new trades."""
    trade = {"guid": "1a", "close_date": None}
    assert process_trade(trade) == trade


def test_process_trade_closed():
    """Test process_trade() for closed trades."""
    # Start with an open trade.
    trade = {"guid": "1a", "close_date": None}
    assert process_trade(trade) == trade

    # The same open trade should not be enqueued.
    assert process_trade(trade) is None

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
