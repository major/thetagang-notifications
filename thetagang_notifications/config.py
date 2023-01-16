"""Configuration for the project."""
import os
from tempfile import mkdtemp

# Base directory for persistent storage.
STORAGE_DIR = os.environ.get("STORAGE_DIR", mkdtemp())
if not os.path.isdir(STORAGE_DIR):
    os.mkdir(STORAGE_DIR)

# thetagang.com URLs
TRADES_JSON_URL = "https://api.thetagang.com/trades"

# Webhook URLs
WEBHOOK_URL_EARNINGS = os.environ.get("WEBHOOK_URL_EARNINGS")
WEBHOOK_URL_TRADES = os.environ.get("WEBHOOK_URL_TRADES")

# API key for secret thetagang.com API endpoints. 😉
TRADES_API_KEY = os.getenv("TRADES_API_KEY")

# Discord username.
DISCORD_USERNAME = "🤠 🤖"
