"""Handle trades on thetagang.com."""
import logging

from discord_webhook import DiscordWebhook, DiscordEmbed
import requests

from thetagang_notifications import config, utils


log = logging.getLogger(__name__)


def download_trades():
    """Download the current list of trades from thetagang.com."""
    resp = requests.get(config.TRADES_JSON_URL)
    trades_json = resp.json()
    return trades_json["data"]["trades"]


def get_webhook_color(trade_type):
    """Provide a color for the webhook based on bullish/bearish strategy."""
    bearish_trades = [
        "CALL CREDIT SPREAD",
        "COVERED CALL",
        "SHORT NAKED CALL",
        "PUT DEBIT SPREAD",
        "LONG NAKED PUT",
        "SELL COMMON STOCK",
    ]
    neutral_trades = [
        "SHORT IRON CONDOR",
        "SHORT STRANGLE",
        "SHORT STRADDLE",
        "LONG STRANGLE",
        "LONG STRADDLE",
    ]
    if trade_type in bearish_trades:
        return "FD3A4A"
    elif trade_type in neutral_trades:
        return "BFAFB2"
    else:
        return "299617"


def get_trade_url(trade):
    """Generate a URL to the trade on thetagang.com."""
    username = trade["User"]["username"]
    return f"https://thetagang.com/{username}/{trade['guid']}"


def parse_trade(trade):
    """Parse a trade and return relevant data."""
    # ⚠ 'match' requires Python 3.10+.
    match trade["type"]:
        case "CASH SECURED PUT":
            return parse_short_put(trade)
        case "SHORT NAKED_CALL" | "COVERED CALL":
            return parse_short_call(trade)
        case _:
            return parse_generic_trade(trade)


def parse_generic_trade(trade):
    """Parse a trade in a generic way that works for all trades."""
    # Set up a dictionary to handle our normalized data.
    normalized = {
        "strikes": utils.gather_strikes(trade),
    }

    return normalized


def parse_short_put(trade):
    """Parse data from a cash secured put."""
    normalized = {
        "strike": f"${trade['short_put']}",
        "breakeven": utils.get_breakeven(trade),
        "return": utils.get_short_put_return(trade),
        "premium": utils.get_pretty_price(trade["price_filled"]),
        "pretty_expiration": utils.get_pretty_expiration(trade["expiry_date"]),
    }
    normalized["annualized_return"] = utils.get_annualized_return(
        normalized["return"], utils.get_dte(trade["expiry_date"])
    )

    return normalized


def parse_short_call(trade):
    """Parse data from a covered call."""
    normalized = {
        "strike": f"${trade['short_call']}",
        "breakeven": utils.get_breakeven(trade),
        "return": utils.get_short_call_return(trade),
        "premium": utils.get_pretty_price(trade["price_filled"]),
        "pretty_expiration": utils.get_pretty_expiration(trade["expiry_date"]),
    }
    normalized["annualized_return"] = utils.get_annualized_return(
        normalized["return"], utils.get_dte(trade["expiry_date"])
    )

    return normalized


def notify_trade(trade, norm, det):
    """Choose the correct notification based on trade type."""
    match trade["type"]:
        case "CASH SECURED PUT":
            notify_cash_secured_put(trade, norm, det)
        case _:
            notify_generic_trade(trade, norm, det)


def notify_cash_secured_put(trade, norm, det):
    """Send a notification for cash secured put trades."""
    qty_string = trade["quantity"] if trade["quantity"] > 1 else "a"
    title = " ".join(
        [
            f"{trade['User']['username']} sold {qty_string}",
            f"{norm['pretty_expiration']} ${trade['symbol']} {norm['strike']}p",
            f"for ${norm['premium']}",
        ]
    )

    embed = DiscordEmbed(
        title=title,
        color=get_webhook_color(trade["type"]),
        url=get_trade_url(trade),
    )
    embed.add_embed_field(name="Breakeven", value=f"${norm['breakeven']}")
    embed.add_embed_field(name="Return %", value=f"{norm['return']}%")
    embed.add_embed_field(name="Annualized %", value=f"{norm['annualized_return']}%")
    embed.set_image(url=utils.get_stock_chart(trade["symbol"]))
    embed.set_footer(text=f"{trade['User']['username']}: {trade['note']}")

    if det["logo_url"]:
        embed.set_thumbnail(url=det["logo_url"])

    send_webhook(embed)


def notify_generic_trade(trade, norm, det):
    """Take parsed trade data and generate a notification."""
    embed = DiscordEmbed(
        title=f"${trade['symbol']}: {trade['type']}",
        color=get_webhook_color(trade["type"]),
        url=get_trade_url(trade),
    )
    embed.add_embed_field(
        name="Expiration", value=utils.get_pretty_expiration(trade["expiry_date"])
    )
    embed.add_embed_field(
        name="Price Filled", value=utils.get_pretty_price(trade["price_filled"])
    )
    embed.add_embed_field(name="Quantity", value=trade["quantity"])
    embed.set_footer(text=f"{trade['User']['username']}: {trade['note']}")

    if det["logo_url"]:
        embed.set_thumbnail(url=det["logo_url"])

    send_webhook(embed)


def send_webhook(embed=None):
    """Send a webhook notification."""
    webhook = DiscordWebhook(
        url=config.WEBHOOK_URL_TRADES,
        rate_limit_retry=True,
        username=config.DISCORD_USERNAME,
    )

    if embed is not None:
        webhook.add_embed(embed)

    return webhook.execute()


def handle_trade(trade):
    """Handle a trade coming from a download."""
    normalized_data = parse_trade(trade)

    # Get data about the company.
    company_details = utils.get_symbol_details(trade["symbol"])

    # Notify the Discord.
    notify_trade(trade, normalized_data, company_details)


if __name__ == "__main__":
    import json

    # with open("tests/assets/trade-short-iron-condor.json", "r") as fileh:
    #     handle_trade(json.load(fileh))

    with open("tests/assets/trade-cash-secured-put.json", "r") as fileh:
        handle_trade(json.load(fileh))
