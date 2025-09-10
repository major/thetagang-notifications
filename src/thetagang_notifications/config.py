"""Configuration for the project using pydantic-settings."""

from pydantic import Field
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
    
    # Webhook URLs
    webhook_url_trades: str = Field(default="missing_webhook_url", description="Discord webhook URL for trades")
    
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


# Create a global settings instance
settings = Settings()

