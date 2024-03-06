"""Configuration for the project."""

import os

# Redis connection details
REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.environ.get("REDIS_PORT", 6379))

# thetagang.com URLs
TRADES_JSON_URL = "https://api3.thetagang.com/trades"

# Spec file with trade properties.
TRADE_SPEC_FILE = "thetagang_notifications/assets/trade_specs.yml"

# Webhook URLs
WEBHOOK_URL_TRADES = os.environ.get("WEBHOOK_URL_TRADES", "missing_webhook_url")

# API key for secret thetagang.com API endpoints. 😉
TRADES_API_KEY = os.getenv("TRADES_API_KEY", "api_key_missing")

# Icons for author line on opening/closing trade notifications.
OPENING_TRADE_ICON = "https://images.emojiterra.com/google/noto-emoji/v2.034/512px/1f680.png"
CLOSING_TRADE_ICON = "https://images.emojiterra.com/google/noto-emoji/v2.034/512px/1f3c1.png"

# Colors for winning, losing, and assigned trades.
COLOR_WINNER = "008000"
COLOR_LOSER = "D42020"
COLOR_ASSIGNED = "FFBF00"

# Emojis for winning, losing, and assigned trades.
EMOJI_WINNER = "✅"
EMOJI_LOSER = "❌"
EMOJI_ASSIGNED = "🚚"

# Wide and trandparent PNG to make the notifications the same width each time:
TRANSPARENT_PNG = "https://major.io/transparent.png"

# Discord username.
DISCORD_USERNAME = "🤠 🤖"

# Some users are patrons but do not regularly participate in Discord.
# We skip their trades.
SKIPPED_USERS = os.environ.get("SKIPPED_USERS", "").split(",")
