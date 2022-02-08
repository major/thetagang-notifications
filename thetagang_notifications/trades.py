"""Handle trades on thetagang.com."""
import logging

from discord_webhook import DiscordWebhook, DiscordEmbed

import pickledb
import requests

from thetagang_notifications import config, utils


log = logging.getLogger(__name__)


def download_trades():
    """Download the current list of trades from thetagang.com."""
    resp = requests.get(config.TRADES_JSON_URL)
    trades_json = resp.json()
    return trades_json["data"]["trades"]


def get_previous_trades():
    """Retrieve old trades from the last run."""
    trades_db = pickledb.load(config.TRADES_DB, True)
    previous_trades = trades_db.get("trades")

    if not previous_trades:
        return []

    return previous_trades


def store_trades(trades):
    """Store the current trades in the database."""
    trade_guids = [x["guid"] for x in trades]
    trades_db = pickledb.load(config.TRADES_DB, True)
    trades_db.set("trades", trade_guids)


def diff_trades(current_trades):
    """Find the trades that are different from the last run."""
    return [x for x in current_trades if x["guid"] not in get_previous_trades()]


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
        case "BUY COMMON STOCK" | "SELL COMMON STOCK":
            return None
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
            notify_short_put(trade, norm, det)
        case "SHORT NAKED_CALL" | "COVERED CALL":
            notify_short_call(trade, norm, det)
        case "BUY COMMON STOCK" | "SELL COMMON STOCK":
            notify_stock_trade(trade, norm, det)
        case _:
            notify_generic_trade(trade, norm, det)


def notify_short_call(trade, norm, det):
    """Send a notification for short call trades."""
    qty_string = f"{trade['quantity']}x" if trade["quantity"] > 1 else "a"
    breakeven = utils.get_pretty_price(norm["breakeven"])
    ptl_return = utils.get_pretty_price(norm["return"])
    ann_return = utils.get_pretty_price(norm["annualized_return"])
    risk = "(covered)" if "COVERED" in trade["type"] else "(naked)"

    title = " ".join(
        [
            f"{trade['User']['username']} sold {qty_string}",
            f"{norm['pretty_expiration']} ${trade['symbol']} {norm['strike']}c {risk}",
            f"for ${norm['premium']}",
        ]
    )

    embed = DiscordEmbed(
        title=title,
        color=get_webhook_color(trade["type"]),
        url=get_trade_url(trade),
    )
    embed.add_embed_field(name="Breakeven", value=f"${breakeven}")
    embed.add_embed_field(name="Return %", value=f"{ptl_return}%")
    embed.add_embed_field(name="Annualized %", value=f"{ann_return}%")
    embed.set_image(url=utils.get_stock_chart(trade["symbol"]))
    embed.set_footer(text=f"{trade['User']['username']}: {trade['note']}")
    embed.set_thumbnail(url=utils.get_stock_logo(trade["symbol"]))

    send_webhook(embed)


def notify_short_put(trade, norm, det):
    """Send a notification for cash secured put trades."""
    qty_string = f"{trade['quantity']}x" if trade["quantity"] > 1 else "a"
    breakeven = utils.get_pretty_price(norm["breakeven"])
    ptl_return = utils.get_pretty_price(norm["return"])
    ann_return = utils.get_pretty_price(norm["annualized_return"])

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
    embed.add_embed_field(name="Breakeven", value=f"${breakeven}")
    embed.add_embed_field(name="Return %", value=f"{ptl_return}%")
    embed.add_embed_field(name="Annualized %", value=f"{ann_return}%")
    embed.set_image(url=utils.get_stock_chart(trade["symbol"]))
    embed.set_footer(text=f"{trade['User']['username']}: {trade['note']}")
    embed.set_thumbnail(url=utils.get_stock_logo(trade["symbol"]))

    send_webhook(embed)


def notify_stock_trade(trade, norm, det):
    """Send a notification for stock trades."""
    action = "bought" if "BUY" in trade["type"] else "sold"
    qty_string = f"{trade['quantity']} shares" if trade["quantity"] > 1 else "1 share"
    title = " ".join(
        [
            f"{trade['User']['username']} {action} {qty_string} of ${trade['symbol']} "
            f"at ${trade['price_filled']} each",
        ]
    )

    embed = DiscordEmbed(
        title=title,
        color=get_webhook_color(trade["type"]),
        url=get_trade_url(trade),
    )
    embed.set_image(url=utils.get_stock_chart(trade["symbol"]))
    embed.set_footer(text=f"{trade['User']['username']}: {trade['note']}")
    embed.set_thumbnail(url=utils.get_stock_logo(trade["symbol"]))

    send_webhook(embed)


def notify_generic_trade(trade, norm, det):
    """Take parsed trade data and generate a notification."""
    embed = DiscordEmbed(
        title=f"${trade['symbol']}: {trade['type']} {norm['strikes']}",
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
    embed.set_image(url=utils.get_stock_chart(trade["symbol"]))
    embed.set_footer(text=f"{trade['User']['username']}: {trade['note']}")
    embed.set_thumbnail(url=utils.get_stock_logo(trade["symbol"]))

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
    # Only notify on Patron trades if configured.
    if config.PATRON_TRADES_ONLY and trade["User"]["role"] != "patron":
        return None

    log.info("Handling trade %s", get_trade_url(trade))

    # Normalize some trade data for easy usage later.
    normalized_data = parse_trade(trade)

    # Get data about the company.
    company_details = utils.get_symbol_details(trade["symbol"])

    # Notify the Discord.
    notify_trade(trade, normalized_data, company_details)


def main():
    """Handle updates for trades."""
    # Get the current list of trades and diff against our previous list.
    current_trades = download_trades()
    new_trades = diff_trades(current_trades)

    # Save the current list of trades to the database.
    store_trades(current_trades)

    # Send an alert for any new trades.
    for trade_record in new_trades:
        handle_trade(trade_record)

    return new_trades
