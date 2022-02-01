"""Handle trades on thetagang.com."""
import requests


from thetagang_notifications import config


def download_trades():
    resp = requests.get(config.TRADES_JSON_URL)
    trades_json = resp.json()
    return trades_json["data"]["trades"]
