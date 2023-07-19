"""Test the trade queue builder."""
import fakeredis
import responses

from thetagang_notifications.trade_queue import TradeQueue


def test_allowed_users() -> None:
    """Verify that we can remove disallowed users from the queue."""
    tq = TradeQueue()
    tq.skipped_users = ["test_user"]

    tq.latest_trades = [
        {"User": {"username": "test_user"}},
        {"User": {"username": "real_user"}},
    ]
    print(tq.allowed_users)
    assert tq.allowed_users == [{"User": {"username": "real_user"}}]


def test_patron_trades() -> None:
    """Verify that we can remove non-patron trades from the queue."""
    tq = TradeQueue()

    tq.latest_trades = [
        {"User": {"role": "patron"}},
        {"User": {"role": "non-patron"}},
    ]
    assert tq.patron_trades == [{"User": {"role": "patron"}}]


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
    trade = {"guid": "1", "close_date": None}
    assert tq.process_trade(trade) == trade

    # If we process the trade again, we should get None.
    assert tq.process_trade(trade) is None

    # Now change the status and verify that we get the trade back.
    trade["close_date"] = "test_date"
    assert tq.process_trade(trade) == trade

    # If we process the trade again, we should get None.
    assert tq.process_trade(trade) is None


def test_build_queue() -> None:
    """Verify that we can build a trade queue."""
    tq = TradeQueue()
    tq.db_conn = fakeredis.FakeRedis(decode_responses=True)

    # Start with a trade we've never seen before.
    trade = {"guid": "1", "close_date": None, "User": {"username": "real_user", "role": "patron"}}
    tq.latest_trades = [trade]
    tq.build_queue()
    assert tq.queued_trades == [trade]

    # If we process the trade again, we should get None.
    tq.build_queue()
    assert tq.queued_trades == []

    # Now change the status and verify that we get the trade back.
    trade["close_date"] = "test_date"
    tq.latest_trades = [trade]
    tq.build_queue()
    assert tq.queued_trades == [trade]

    # If we process the trade again, we should get None.
    tq.build_queue()
    assert tq.queued_trades == []


@responses.activate
def test_update_trades() -> None:
    """Test getting updated trades from thetagang.com."""
    mocked_trades = {
        "data": {
            "trades": [
                {"guid": "1", "close_date": None, "User": {"username": "real_user", "role": "patron"}},
                {"guid": "2", "close_date": None, "User": {"username": "real_user", "role": "patron"}},
            ]
        }
    }

    recent_trades = responses.get(url="https://api.thetagang.com/v1/trades", json=mocked_trades, status=200)
    responses.add(recent_trades)

    tq = TradeQueue()
    tq.update_trades()
    assert tq.latest_trades == list(reversed(mocked_trades["data"]["trades"]))
