#!/usr/bin/env python
"""Retrieve and handle data from thetagang.com."""
from datetime import datetime
from dateutil import parser
import logging

import requests

log = logging.getLogger(__name__)


def day_diff(trade_date):
    """Find different in days between a date and right now."""
    trade_date = parser.parse(trade_date).replace(tzinfo=None)
    now = datetime.utcnow()
    return (now - trade_date).days


def filter_recent(trades):
    """Limit trades to the most recent ones."""
    valid_trades = [x for x in trades if day_diff(x['updatedAt']) <= 2]

    return valid_trades


def get_patron_trades():
    """Get all patron trades on the site."""
    trades = []
    for profile in get_profiles():
        trades += get_trades(profile)

    return filter_recent(trades)


def get_profiles():
    """Get the list of patreon usernames."""
    log.info("Getting list of patrons...")
    resp = requests.get("https://api.thetagang.com/profiles")
    raw = resp.json()

    return [x['username'] for x in raw['data']['users']]


def get_single_trade(guid):
    """Get a single trade."""
    log.info("Downloading trade: %s", guid)
    url = f"https://api.thetagang.com/trades/{guid}"
    resp = requests.get(url)

    return resp.json()['data']['trade']


def get_trades(username=None):
    """Get trades for a user or for everyone."""
    log.info("Downloading trades: username=%s", username)
    params = {} if not username else {"username": username}
    url = "https://api.thetagang.com/trades"
    resp = requests.get(url, params)

    # Reverse the list to examine the oldest trades first. We want to notify on
    # older closed trades before notifying on new ones. This helps a lot with
    # rolled options contracts so we show the closed one first and then the
    # opened one.
    trades = resp.json()['data']['trades']
    trades.reverse()

    return trades
