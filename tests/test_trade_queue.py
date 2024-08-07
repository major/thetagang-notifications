"""Test the trade queue builder."""

from datetime import datetime, timedelta, timezone

import fakeredis

from thetagang_notifications.trade_queue import TradeQueue


def test_store_trade() -> None:
    """Verify that we can store a trade in the database."""
    tq = TradeQueue()
    tq.db_conn = fakeredis.FakeRedis(decode_responses=True)

    # Try it with a closed trade.
    trade = {"guid": "1", "close_date": "test_date"}
    tq.store_trade(trade)
    assert tq.db_conn.get("1") == "closed"

    # Try it with an open trade.
    trade = {"guid": "2", "close_date": None}
    tq.store_trade(trade)
    assert tq.db_conn.get("2") == "open"


def test_trade_has_new_status() -> None:
    """Verify we can detect when a trade has a new status."""
    tq = TradeQueue()
    tq.db_conn = fakeredis.FakeRedis(decode_responses=True)

    # Start with a trade we've never seen before.
    trade = {"guid": "1", "close_date": None}
    assert tq.trade_has_new_status(trade)

    # Now store it and verify that we don't see a new status.
    tq.store_trade(trade)
    assert not tq.trade_has_new_status(trade)

    # Now change the status and verify that we see a new status.
    trade["close_date"] = "test_date"
    assert tq.trade_has_new_status(trade)


def test_trade_exists() -> None:
    """Verify we can detect if a trade exists."""
    tq = TradeQueue()
    tq.db_conn = fakeredis.FakeRedis(decode_responses=True)

    # Start with a trade we've never seen before.
    trade = {"guid": "1", "close_date": None}
    assert not tq.trade_exists(trade)

    # Now store it and verify that we see it.
    tq.store_trade(trade)
    assert tq.trade_exists(trade)


def test_process_trade() -> None:
    """Verify we can process trades into the queue."""
    tq = TradeQueue()
    tq.db_conn = fakeredis.FakeRedis(decode_responses=True)

    # Start with a trade we've never seen before.
    updated_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    trade = {
        "guid": "1",
        "close_date": None,
        "updatedAt": updated_at,
    }
    assert tq.process_trade(trade) == trade

    # If we process the trade again, we should get None.
    assert tq.process_trade(trade) is None

    # Now change the status and verify that we get the trade back.
    trade["close_date"] = "test_date"
    assert tq.process_trade(trade) == trade

    # If we process the trade again, we should get None.
    assert tq.process_trade(trade) is None

    # Finally, try a new trade with a very old date.
    updated_at = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    trade = {
        "guid": "2",
        "close_date": None,
        "updatedAt": updated_at,
    }
    assert tq.process_trade(trade) is None


def test_build_queue() -> None:
    """Verify that we can build a trade queue."""
    tq = TradeQueue()
    tq.db_conn = fakeredis.FakeRedis(decode_responses=True)

    # Start with a trade we've never seen before.
    updated_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    trade = {
        "guid": "1",
        "close_date": None,
        "updatedAt": updated_at,
        "mistake": False,
        "User": {"username": "real_user", "role": "patron"},
    }
    tq.latest_trades = [trade]
    assert tq.build_queue() == [trade]

    # If we process the trade again, we should get None.
    assert tq.build_queue() == []

    # Now change the status and verify that we get the trade back.
    trade["close_date"] = "test_date"
    tq.latest_trades = [trade]
    assert tq.build_queue() == [trade]

    # If we process the trade again, we should get None.
    assert tq.build_queue() == []


def test_trade_is_old() -> None:
    """Test detection of an old trade."""
    tq = TradeQueue()
    trade = {"guid": "1", "updatedAt": "2021-01-01T00:00:00Z"}
    assert tq.trade_is_old(trade)

    trade["updatedAt"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    assert not tq.trade_is_old(trade)


# def test_update_trades() -> None:
#     """Test getting updated trades from thetagang.com."""
#     mocked_trades = {
#         "data": [
#             {"guid": "1", "close_date": None, "mistake": False, "User": {"username": "real_user", "role": "patron"}},
#             {"guid": "2", "close_date": None, "mistake": False, "User": {"username": "real_user", "role": "patron"}},
#         ]
#     }

#     recent_trades = responses.get(url="https://api3.thetagang.com/api/patrons", json=mocked_trades, status=200)
#     responses.add(recent_trades)

#     tq = TradeQueue()
#     tq.update_trades()
#     assert tq.latest_trades == list(reversed(mocked_trades["data"]))
