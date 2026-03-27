"""Binance crypto trading bot.

Usage
-----
    # Dry-run (no real orders placed):
    python bot.py

    # Live trading (requires valid API keys in .env):
    DRY_RUN=false python bot.py

The bot fetches historical candlestick data from Binance, runs the
configured strategy, and places BUY/SELL market orders accordingly.
"""

import logging
import time
from typing import Optional

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

from config import Config
from strategy import BaseStrategy, SMAStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Map human-readable interval strings to Binance Client constants.
INTERVAL_MAP: dict[str, str] = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "30m": Client.KLINE_INTERVAL_30MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY,
}


class BinanceBot:
    """Main trading bot that connects to Binance and executes a strategy.

    Parameters
    ----------
    config:
        Bot configuration.  Defaults to a new :class:`~config.Config`
        instance (which reads from environment variables).
    strategy:
        The trading strategy to use.  Defaults to
        :class:`~strategy.SMAStrategy`.
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        strategy: Optional[BaseStrategy] = None,
    ) -> None:
        self.config = config or Config()
        self.config.validate()
        self.strategy = strategy or SMAStrategy()
        self.client = Client(self.config.api_key, self.config.api_secret)
        self._interval = INTERVAL_MAP.get(self.config.interval, Client.KLINE_INTERVAL_1HOUR)

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    def fetch_klines(self, limit: int = 100) -> pd.DataFrame:
        """Return the last *limit* closed candles as a DataFrame."""
        raw = self.client.get_klines(
            symbol=self.config.symbol,
            interval=self._interval,
            limit=limit,
        )
        df = pd.DataFrame(
            raw,
            columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "num_trades",
                "taker_buy_base_vol", "taker_buy_quote_vol", "ignore",
            ],
        )
        df["close"] = df["close"].astype(float)
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df

    # ------------------------------------------------------------------
    # Order execution
    # ------------------------------------------------------------------

    def _place_order(self, side: str) -> None:
        """Place a market order (or log it when in dry-run mode)."""
        symbol = self.config.symbol
        qty = self.config.trade_quantity

        if self.config.dry_run:
            logger.info("[DRY RUN] Would place %s order: %s qty=%s", side, symbol, qty)
            return

        try:
            if side == "BUY":
                order = self.client.order_market_buy(symbol=symbol, quantity=qty)
            else:
                order = self.client.order_market_sell(symbol=symbol, quantity=qty)
            logger.info("Order placed: %s", order)
        except BinanceAPIException as exc:
            logger.error("Failed to place %s order: %s", side, exc)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run_once(self) -> str:
        """Fetch latest data, evaluate strategy, and act on the signal.

        Returns the signal string (``"BUY"``, ``"SELL"``, or ``"HOLD"``).
        """
        df = self.fetch_klines()
        signal = self.strategy.generate_signal(df)
        logger.info("Symbol=%s  Signal=%s", self.config.symbol, signal)

        if signal in ("BUY", "SELL"):
            self._place_order(signal)

        return signal

    def run(self, poll_interval_seconds: int = 60) -> None:
        """Continuously run the bot, sleeping *poll_interval_seconds* between ticks."""
        mode = "DRY RUN" if self.config.dry_run else "LIVE"
        logger.info(
            "Starting bot | symbol=%s  interval=%s  strategy=%s  mode=%s",
            self.config.symbol,
            self.config.interval,
            type(self.strategy).__name__,
            mode,
        )
        try:
            while True:
                try:
                    self.run_once()
                except BinanceAPIException as exc:
                    logger.error("Binance API error: %s", exc)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Unexpected error: %s", exc)

                time.sleep(poll_interval_seconds)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")


if __name__ == "__main__":
    bot = BinanceBot()
    bot.run()
