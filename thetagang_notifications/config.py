"""Configuration for the project."""
import os

# Base directory for persistent storage.
STORAGE_DIR = "/data"

# thetagang.com URLs
TRADES_JSON_URL = "https://api.thetagang.com/trades"
TRENDS_JSON_URL = "https://api.thetagang.com/trends"

# Database locations.
TRADES_DB = f"{STORAGE_DIR}/trades.db"
TRENDS_DB = f"{STORAGE_DIR}/trends.db"

# Webhook URLs
WEBHOOK_URL_TRADES = os.environ.get("WEBHOOK_URL_TRADES", None)
WEBHOOK_URL_TRENDS = os.environ.get("WEBHOOK_URL_TRENDS", None)
