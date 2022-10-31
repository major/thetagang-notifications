#!/usr/bin/env python
"""Retrieve and handle data from thetagang.com."""
import logging
import tempfile
from datetime import datetime
from time import sleep

import requests
from dateutil import parser
from playwright.sync_api import sync_playwright

log = logging.getLogger(__name__)


def day_diff(trade_date):
    """Find different in days between a date and right now."""
    trade_date = parser.parse(trade_date).replace(tzinfo=None)
    now = datetime.utcnow()
    return (now - trade_date).days


def filter_recent(trades):
    """Limit trades to the most recent ones."""
    return [x for x in trades if day_diff(x["updatedAt"]) <= 2]


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

    return [x["username"] for x in raw["data"]["users"]]


def get_single_trade(guid):
    """Get a single trade."""
    log.info("Downloading trade: %s", guid)
    url = f"https://api.thetagang.com/trades/{guid}"
    resp = requests.get(url)

    return resp.json()["data"]["trade"]


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
    trades = resp.json()["data"]["trades"]
    trades.reverse()

    return trades


def get_trade_screenshot(guid):
    """Get a screenshot of a trade from thetagang.com."""
    log.info("Getting trade screenshot: %s", guid)
    trade = get_single_trade(guid)
    username = trade["User"]["username"]
    url = f"https://thetagang.com/{username}/{guid}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        page = context.new_page()
        page.goto(url)

        # Get the release notes out of the way.
        page.locator("text=RELEASE NOTES").click()
        page.locator('div[role="dialog"]').press("Escape")

        # Wait two seconds before getting the screenshot.
        sleep(2)

        # Screenshot the div with the trade in it.
        temp_dir = tempfile.TemporaryDirectory().name
        screenshot_path = f"{temp_dir}/{guid}.png"
        css_locator = ".col-xl-6 > div:nth-child(1) > div:nth-child(1)"
        page.locator(css_locator).screenshot(path=screenshot_path)

        browser.close()

    return screenshot_path
