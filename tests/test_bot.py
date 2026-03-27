"""Unit tests for the BinanceBot class."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from bot import BinanceBot
from config import Config
from strategy import SMAStrategy


def _dry_run_config(**kwargs) -> Config:
    """Return a Config with dry_run=True and dummy credentials."""
    defaults = dict(
        api_key="test_key",
        api_secret="test_secret",
        symbol="BTCUSDT",
        interval="1h",
        trade_quantity=0.001,
        dry_run=True,
    )
    defaults.update(kwargs)
    return Config(**defaults)


def _sample_klines_df(num_rows: int = 50) -> pd.DataFrame:
    """Return a DataFrame that mimics what ``fetch_klines`` produces."""
    closes = [float(100 + i) for i in range(num_rows)]
    return pd.DataFrame({
        "open_time": range(num_rows),
        "open": closes,
        "high": closes,
        "low": closes,
        "close": closes,
        "volume": [1.0] * num_rows,
        "close_time": range(num_rows),
        "quote_asset_volume": [0.0] * num_rows,
        "num_trades": [0] * num_rows,
        "taker_buy_base_vol": [0.0] * num_rows,
        "taker_buy_quote_vol": [0.0] * num_rows,
        "ignore": [None] * num_rows,
    })


@pytest.fixture()
def bot_with_mock_client():
    """Return a BinanceBot whose Binance client is replaced by a MagicMock."""
    config = _dry_run_config()
    with patch("bot.Client") as MockClient:
        mock_client_instance = MagicMock()
        MockClient.return_value = mock_client_instance
        bot = BinanceBot(config=config, strategy=SMAStrategy())
        bot.client = mock_client_instance
        yield bot, mock_client_instance


class TestConfig:
    def test_dry_run_does_not_require_keys(self):
        cfg = Config(api_key="", api_secret="", dry_run=True)
        cfg.validate()  # Should not raise

    def test_live_mode_requires_api_key(self):
        cfg = Config(api_key="", api_secret="secret", dry_run=False)
        with pytest.raises(ValueError, match="BINANCE_API_KEY"):
            cfg.validate()

    def test_live_mode_requires_api_secret(self):
        cfg = Config(api_key="key", api_secret="", dry_run=False)
        with pytest.raises(ValueError, match="BINANCE_API_SECRET"):
            cfg.validate()

    def test_invalid_trade_quantity(self):
        cfg = Config(trade_quantity=0, dry_run=True)
        with pytest.raises(ValueError, match="TRADE_QUANTITY"):
            cfg.validate()


class TestBinanceBot:
    def test_run_once_returns_signal(self, bot_with_mock_client):
        bot, mock_client = bot_with_mock_client
        # Provide raw klines data (12 fields per row) as the API would
        sample_df = _sample_klines_df(50)
        raw_klines = sample_df.values.tolist()
        mock_client.get_klines.return_value = raw_klines

        signal = bot.run_once()
        assert signal in ("BUY", "SELL", "HOLD")

    def test_dry_run_does_not_call_order_api(self, bot_with_mock_client):
        bot, mock_client = bot_with_mock_client
        sample_df = _sample_klines_df(50)
        raw_klines = sample_df.values.tolist()
        mock_client.get_klines.return_value = raw_klines

        bot.run_once()

        mock_client.order_market_buy.assert_not_called()
        mock_client.order_market_sell.assert_not_called()

    def test_fetch_klines_returns_dataframe(self, bot_with_mock_client):
        bot, mock_client = bot_with_mock_client
        sample_df = _sample_klines_df(10)
        raw_klines = sample_df.values.tolist()
        mock_client.get_klines.return_value = raw_klines

        result = bot.fetch_klines(limit=10)
        assert isinstance(result, pd.DataFrame)
        assert "close" in result.columns
        assert len(result) == 10
