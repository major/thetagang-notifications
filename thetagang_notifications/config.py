"""Configuration for the project."""
import os
from tempfile import mkdtemp

# Base directory for persistent storage.
STORAGE_DIR = os.environ.get("STORAGE_DIR", mkdtemp())
if not os.path.isdir(STORAGE_DIR):
    os.mkdir(STORAGE_DIR)

# thetagang.com URLs
TRADES_JSON_URL = "https://api.thetagang.com/trades"
TRENDS_JSON_URL = "https://api.thetagang.com/trends"

# Unified databases using tables in a sqlite DB.
MAIN_DB = f"{STORAGE_DIR}/thetagang-notifications.db"

# Unified databases using tinydb.
MAIN_TINYDB = f"{STORAGE_DIR}/thetagang-notifications.tinydb"

# Webhook URLs
WEBHOOK_URL_EARNINGS = os.environ.get("WEBHOOK_URL_EARNINGS")
WEBHOOK_URL_TRADES = os.environ.get("WEBHOOK_URL_TRADES")
WEBHOOK_URL_TRADE_SCREENSHOTS = os.environ.get("WEBHOOK_URL_TRADE_SCREENSHOTS", None)
WEBHOOK_URL_TRENDS = os.environ.get("WEBHOOK_URL_TRENDS")

# Twitter credentials.
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Discord username.
DISCORD_USERNAME = "🤠 🤖"
