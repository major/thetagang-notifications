"""Handle trades on thetagang.com."""
import logging

from discord_webhook import DiscordWebhook, DiscordEmbed
import pickledb
import requests

from thetagang_notifications import config, utils


log = logging.getLogger(__name__)


def download_trends():
    """Get latest trends from thetagang.com."""
    resp = requests.get(config.TRENDS_JSON_URL)
    trades_json = resp.json()
    return trades_json["data"]["trends"]


def get_previous_trends():
    """Retrieve old trends from the last run."""
    trends_db = pickledb.load(config.TRENDS_DB, True)
    previous_trends = trends_db.get("trends")

    if not previous_trends:
        return []

    return previous_trends


def get_discord_description(data):
    """Generate a Discord notification description based on stock data."""
    description = f"{data['longName']}\n" f"{data['sector']} - {data['industry']}"

    return description


def store_trends(trends):
    """Store the current trends in the database."""
    trends_db = pickledb.load(config.TRENDS_DB, True)
    trends_db.set("trends", trends)


def diff_trends(current_trends):
    """Find the trends that are different from the last run."""
    return list(set(current_trends) - set(get_previous_trends()))


def notify_discord(trending_symbol):
    """Send an alert to Discord for a trending symbol."""
    stock_details = utils.get_symbol_details(trending_symbol)

    if "sector" not in stock_details.keys():
        log.info("📈 Sending basic trend notification for %s", trending_symbol)
        return notify_discord_basic(stock_details)

    log.info("📈 Sending fancy trend notification for %s", trending_symbol)
    return notify_discord_fancy(stock_details)


def notify_discord_basic(stock_details):
    """Send a basic alert to Discord."""
    webhook = DiscordWebhook(
        url=config.WEBHOOK_URL_TRENDS,
        rate_limit_retry=True,
        content=f"{stock_details['symbol']} added to trending tickers",
        username=config.DISCORD_USERNAME,
    )
    return webhook.execute()


def notify_discord_fancy(stock_details):
    """Send a fancy alert to Discord."""
    webhook = DiscordWebhook(
        url=config.WEBHOOK_URL_TRENDS,
        rate_limit_retry=True,
        username=config.DISCORD_USERNAME,
    )
    embed = DiscordEmbed(
        title=f"{stock_details['symbol']} added to trending tickers",
        color="AFE1AF",
        description=get_discord_description(stock_details),
    )
    embed.set_image(url=utils.get_stock_chart(stock_details["symbol"]))
    embed.set_thumbnail(url=stock_details["logo_url"])
    webhook.add_embed(embed)
    return webhook.execute()


def main():
    """Handle updates for trends."""
    # Get the current list of trends and diff against our previous list.
    current_trends = download_trends()
    new_trends = diff_trends(current_trends)

    # Save the current list of trends to the database.
    store_trends(current_trends)

    # Send an alert for any new trends.
    for trending_symbol in sorted(new_trends):
        notify_discord(trending_symbol)

    return new_trends
