#!/usr/bin/env python
"""Retrieve data from thetagang.com using a secret optimized method."""
import logging

import requests

from thetagang_notifications import config

log = logging.getLogger(__name__)


def get_trades():
    """Get the most recently updated trades."""
    params = {"api_key": config.TRADES_API_KEY}
    url = "https://api.thetagang.com/v1/trades"
    resp = requests.get(url, params)

    # Reverse the list to examine the oldest trades first. We want to notify on
    # older closed trades before notifying on new ones. This helps a lot with
    # rolled options contracts so we show the closed one first and then the
    # opened one.
    trades = resp.json()["data"]["trades"]
    trades.reverse()

    return trades
