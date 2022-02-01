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

# Database locations.
TRADES_DB = f"{STORAGE_DIR}/trades.db"
TRENDS_DB = f"{STORAGE_DIR}/trends.db"

# Webhook URLs
WEBHOOK_URL_TRADES = os.environ.get("WEBHOOK_URL_TRADES")
WEBHOOK_URL_TRENDS = os.environ.get("WEBHOOK_URL_TRENDS")
