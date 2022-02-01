"""Handle trades on thetagang.com."""
import logging

log = logging.getLogger(__name__)

from discord_webhook import DiscordWebhook, DiscordEmbed
import pickledb
import requests


from thetagang_notifications import config, utils


def download_trends():
    """Get latest trends from thetagang.com."""
    log.info(f"Getting latest trends from {config.TRENDS_JSON_URL}")
    resp = requests.get(config.TRENDS_JSON_URL)
    trades_json = resp.json()
    return trades_json["data"]["trends"]


def get_previous_trends():
    """Retrieve old trends from the last run."""
    db = pickledb.load(config.TRENDS_DB, True)
    previous_trends = db.get("trends")

    if not previous_trends:
        return []

    return previous_trends


def get_discord_description(d):
    """Generate a Discord notification description based on stock data."""
    description = f"{d['Company']}\n" f"{d['Sector']} - {d['Industry']}"
    if "Earnings" in d.keys() and d["Earnings"] != "-":
        description += f"\nEarnings: {d['Earnings']}"

    return description


def store_trends(trends):
    """Store the current trends in the database."""
    db = pickledb.load(config.TRENDS_DB, True)
    db.set("trends", trends)


def diff_trends(current_trends):
    """Find the trends that are different from the last run."""
    return list(set(current_trends) - set(get_previous_trends()))


def notify_discord(trending_symbol):
    """Send an alert to Discord for a trending symbol."""
    stock_details = utils.get_symbol_details(trending_symbol)

    if "Company" not in stock_details.keys():
        log.info(f"Sending basic trend notification for {trending_symbol}")
        return notify_discord_basic(stock_details)

    log.info(f"Sending fancy trend notification for {trending_symbol}")
    return notify_discord_fancy(stock_details)


def notify_discord_basic(stock_details):
    """Send a basic alert to Discord."""
    webhook = DiscordWebhook(
        url=config.WEBHOOK_URL_TRENDS,
        rate_limit_retry=True,
        content=f"{stock_details['Symbol']} added to trending tickers",
    )
    return webhook.execute()


def notify_discord_fancy(stock_details):
    """Send a fancy alert to Discord."""
    webhook = DiscordWebhook(url=config.WEBHOOK_URL_TRENDS, rate_limit_retry=True)
    embed = DiscordEmbed(
        title=f"{stock_details['Symbol']} added to trending tickers",
        color="AFE1AF",
        description=get_discord_description(stock_details),
    )
    embed.set_image(url=utils.get_stock_chart(stock_details["Symbol"]))
    embed.set_thumbnail(url=utils.get_stock_logo(stock_details["Symbol"]))
    webhook.add_embed(embed)
    return webhook.execute()


def main():
    """Handle updates for trends."""
    print("MAINNNNNNNNNNNN")
    # Get the current list of trends and diff against our previous list.
    current_trends = download_trends()
    new_trends = diff_trends(current_trends)
    log.info(f"New trends: {new_trends}")

    # Save the current list of trends to the database.
    store_trends(current_trends)

    # Send an alert for any new trends.
    for trending_symbol in sorted(new_trends):
        notify_discord(trending_symbol)

    return new_trends
