"""Tests for thetaget functions."""
from unittest.mock import MagicMock, patch

from thetagang_notifications import thetaget_v2

MOCKED_TRADES = {
    "status": 200,
    "data": {
        "trades": [
            {
                "pl": 0,
                "guid": "b9d6fe39-c4e6-49e1-a142-a851f50b4935",
                "expiry_date": "2023-02-17T08:00:00.000Z",
                "close_date": None,
                "open_date": "2023-01-06T22:01:47.185Z",
                "symbol": "GOOGL",
                "initial": False,
                "quantity": 1,
                "type": "CASH SECURED PUT",
                "payment": "credit",
                "win": None,
                "user_guid": "8667df67-8610-4303-a175-021039315a8c",
                "tag": None,
                "short_put": "80",
                "long_put": None,
                "short_call": None,
                "long_call": None,
                "price_filled": 1.86,
                "price_closed": None,
                "open_quote": 87.33,
                "close_quote": None,
                "assigned": None,
                "earnings": False,
                "tweet_id": None,
                "opened_during_market_hours": None,
                "closed_during_market_hours": None,
                "closed_before_expiration": None,
                "note": "Adding some bullishness to balance out my portfolio ",
                "closing_note": None,
                "createdAt": "2023-01-06T22:01:47.185Z",
                "updatedAt": "2023-01-06T22:01:48.078Z",
                "stock_guid": None,
                "Actions": [],
                "Posts": [],
                "User": {
                    "username": "jrue",
                    "flair": None,
                    "role": "member",
                    "streak": 35,
                    "verified": True,
                },
            }
        ]
    },
}


@patch("thetagang_notifications.thetaget_v2.requests.get")
def test_get_trades(mock_requests):
    """Get all recently updated trades."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCKED_TRADES
    mock_requests.return_value = mock_response

    trades = thetaget_v2.get_trades()

    assert type(trades) == list
    assert trades[0]["updatedAt"] == "2023-01-06T22:01:48.078Z"
