#!/usr/bin/env python
"""Retrieve and handle data from thetagang.com."""
import requests


def get_patron_trades():
    """Get all patron trades on the site."""
    trades = []
    for profile in get_profiles():
        trades += get_trades(profile)

    return trades


def get_profiles():
    """Get the list of patreon usernames."""
    resp = requests.get("https://api.thetagang.com/profiles")
    raw = resp.json()

    return [x['username'] for x in raw['data']['users']]


def get_single_trade(guid):
    """Get a single trade."""
    url = f"https://api.thetagang.com/trades/{guid}"
    resp = requests.get(url)

    return resp.json()['data']['trade']


def get_trades(username=None):
    """Get trades for a user or for everyone."""
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
