"""Handle trades on thetagang.com."""
from discord_webhook import DiscordWebhook, DiscordEmbed
import pickledb
import requests


from thetagang_notifications import config, utils


def download_trends():
    """Get latest trends from thetagang.com."""
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


def store_trends(trends):
    """Store the current trends in the database."""
    db = pickledb.load(config.TRENDS_DB, True)
    db.set("trends", trends)


def diff_trends(current_trends):
    """Find the trends that are different from the last run."""
    return set(current_trends) - set(get_previous_trends())


def notify_discord(trending_symbol):
    """Send an alert to Discord for a trending symbol."""
    stock_details = utils.get_symbol_details(trending_symbol)

    if not stock_details:
        return notify_discord_basic(stock_details)

    return notify_discord_fancy(stock_details)


def notify_discord_basic(stock_details):
    """Send a basic alert to Discord."""
    webhook = DiscordWebhook(
        url=config.WEBHOOK_URL_TRENDS,
        rate_limit_retry=True,
        content=f"New trending ticker: {stock_details['Symbol']}",
    )
    return webhook.execute()


def notify_discord_fancy(stock_details):
    """Send a fancy alert to Discord."""
    webhook = DiscordWebhook(url=config.WEBHOOK_URL_TRENDS, rate_limit_retry=True)
    embed = DiscordEmbed(
        title=f"New trending ticker: {stock_details['Symbol']}",
        color="AFE1AF",
        description=(
            f"{stock_details['Company']} "
            f"({stock_details['Sector']} - {stock_details['Industry']})\n"
            f"Earnings: {stock_details['Earnings']}"
        ),
    )
    embed.set_image(url=stock_details["Chart"])
    embed.set_thumbnail(url=stock_details["Logo"])
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
    for trending_symbol in new_trends:
        notify_discord(trending_symbol)
