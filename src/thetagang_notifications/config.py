"""Configuration for the project using pydantic-settings."""

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using pydantic-settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Redis connection details
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")

    # thetagang.com URLs
    trades_json_url: str = Field(default="https://api3.thetagang.com/trades", description="Trades API URL")

    # Spec file with trade properties
    trade_spec_file: str = Field(default="src/thetagang_notifications/assets/trade_specs.yml", description="Trade spec file path")

    # Webhook URLs - supports multiple webhooks 🎯
    webhook_url_trades: str | None = Field(
        default="missing_webhook_url",
        description="Discord webhook URL for trades (deprecated, use webhook_url_trades_list)"
    )
    webhook_url_trades_list: str | None = Field(
        default=None,
        description="Comma-separated Discord webhook URLs for trades"
    )

    # API key for secret thetagang.com API endpoints
    trades_api_key: str = Field(default="api_key_missing", description="ThetaGang API key")
    
    # Icons for author line on opening/closing trade notifications
    opening_trade_icon: str = Field(
        default="https://images.emojiterra.com/google/noto-emoji/v2.034/512px/1f680.png",
        description="Opening trade icon URL"
    )
    closing_trade_icon: str = Field(
        default="https://images.emojiterra.com/google/noto-emoji/v2.034/512px/1f3c1.png", 
        description="Closing trade icon URL"
    )
    
    # Colors for winning, losing, and assigned trades
    color_winner: str = Field(default="008000", description="Color for winning trades")
    color_loser: str = Field(default="D42020", description="Color for losing trades")
    color_assigned: str = Field(default="FFBF00", description="Color for assigned trades")
    
    # Emojis for winning, losing, and assigned trades
    emoji_winner: str = Field(default="✅", description="Emoji for winning trades")
    emoji_loser: str = Field(default="❌", description="Emoji for losing trades")
    emoji_assigned: str = Field(default="🚚", description="Emoji for assigned trades")
    
    # Wide and transparent PNG to make the notifications the same width each time
    transparent_png: str = Field(default="https://major.io/transparent.png", description="Transparent PNG URL")
    
    # Discord username
    discord_username: str = Field(default="🤠 🤖", description="Discord bot username")
    
    # Some users are patrons but do not regularly participate in Discord
    # We skip their trades (comma-separated list)
    skipped_users: str = Field(default="", description="Comma-separated list of users to skip")
    
    @property
    def skipped_users_list(self) -> list[str]:
        """Return skipped users as a list."""
        return [user.strip() for user in self.skipped_users.split(",") if user.strip()]

    @model_validator(mode="after")
    def validate_webhook_config(self) -> "Settings":
        """
        🔍 Validate Discord webhook configuration.

        Ensures at least one valid Discord webhook URL is provided (either via
        webhook_url_trades or webhook_url_trades_list). This maintains backward
        compatibility while supporting the new multi-webhook feature.

        Returns:
            Self with validated webhook configuration

        Raises:
            ValueError: If no valid webhook URLs are configured
        """
        # Allow the default "missing_webhook_url" to pass validation for testing
        # but warn if it's the only URL provided in production
        if (not self.webhook_url_trades or self.webhook_url_trades == "missing_webhook_url") and not self.webhook_url_trades_list:
            # Only raise error if we're not using the default test value
            if self.webhook_url_trades != "missing_webhook_url":
                msg = (
                    "At least one Discord webhook URL must be provided via "
                    "WEBHOOK_URL_TRADES or WEBHOOK_URL_TRADES_LIST"
                )
                raise ValueError(msg)
        return self

    def get_webhook_urls(self) -> list[str]:
        """
        📋 Get list of Discord webhook URLs from configuration.

        Combines both the legacy single URL (webhook_url_trades) and the new
        comma-separated URLs (webhook_url_trades_list) into a single list.

        Returns:
            List of Discord webhook URLs (deduplicated and stripped)

        Example:
            >>> settings.webhook_url_trades = "https://discord.com/api/webhooks/1"
            >>> settings.webhook_url_trades_list = "https://discord.com/api/webhooks/2,https://discord.com/api/webhooks/3"
            >>> settings.get_webhook_urls()
            ['https://discord.com/api/webhooks/1', 'https://discord.com/api/webhooks/2', 'https://discord.com/api/webhooks/3']
        """
        urls: list[str] = []

        # Add legacy single URL if present
        if self.webhook_url_trades:
            urls.append(self.webhook_url_trades.strip())

        # Add comma-separated URLs if present
        if self.webhook_url_trades_list:
            # Split by comma and strip whitespace
            new_urls = [url.strip() for url in self.webhook_url_trades_list.split(",")]
            # Filter out empty strings
            new_urls = [url for url in new_urls if url]
            urls.extend(new_urls)

        # Deduplicate while preserving order
        seen: set[str] = set()
        deduplicated: list[str] = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                deduplicated.append(url)

        return deduplicated


# Create a global settings instance
settings = Settings()

