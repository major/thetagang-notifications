#!/usr/bin/env python3
"""Make a test notification for any trade guid from thetagang.com."""
import sys

import requests
import yaml

from thetagang_notifications.config import TRADE_SPEC_FILE
from thetagang_notifications.trade import get_notifier


def download_trade(trade_guid):
    """Download the trade from thetagang.com."""
    response = requests.get(f"https://api.thetagang.com/trades/{trade_guid}", timeout=15)
    return response.json()["data"]["trade"]


def make_notification(trade_guid):
    """Make a notification for the trade."""
    trade = download_trade(trade_guid)
    trade_obj = get_notifier(trade)
    trade_obj.notify()


def get_all_guids():
    """Get all guids from thetagang.com."""
    with open(TRADE_SPEC_FILE, encoding="utf-8") as file_handle:
        spec_data = yaml.safe_load(file_handle)
    return [x["example_guid"] for x in spec_data]


if __name__ == "__main__":
    try:
        guids = [sys.argv.pop(1)]
    except IndexError:
        guids = get_all_guids()

    for guid in guids:
        make_notification(guid)
