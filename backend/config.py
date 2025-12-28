from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""

    # Binance API
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_TO: str = ""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Application
    DATABASE_URL: str = "sqlite:///./data/screener.db"
    LOG_LEVEL: str = "INFO"
    UPDATE_INTERVAL: int = 300

    # Thresholds
    MIN_VOLUME_USD: float = 1000000
    MIN_PRICE_CHANGE_5M: float = 2.0
    MIN_PRICE_CHANGE_15M: float = 3.0
    BETA_THRESHOLD: float = 1.2

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
