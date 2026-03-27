"""Configuration management for the Binance trading bot.

Reads settings from environment variables (or a .env file) and exposes
them as a typed ``Config`` dataclass so every other module imports from
one authoritative source.
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    api_key: str = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("BINANCE_API_SECRET", ""))
    symbol: str = field(default_factory=lambda: os.getenv("TRADING_SYMBOL", "BTCUSDT"))
    interval: str = field(default_factory=lambda: os.getenv("TRADING_INTERVAL", "1h"))
    trade_quantity: float = field(
        default_factory=lambda: float(os.getenv("TRADE_QUANTITY", "0.001"))
    )
    dry_run: bool = field(
        default_factory=lambda: os.getenv("DRY_RUN", "true").lower() == "true"
    )

    def validate(self) -> None:
        """Raise ``ValueError`` when required fields are missing (live mode only)."""
        if not self.dry_run:
            if not self.api_key:
                raise ValueError("BINANCE_API_KEY is required when DRY_RUN=false")
            if not self.api_secret:
                raise ValueError("BINANCE_API_SECRET is required when DRY_RUN=false")
        if self.trade_quantity <= 0:
            raise ValueError("TRADE_QUANTITY must be greater than 0")
