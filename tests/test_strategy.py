"""Unit tests for trading strategies."""

import pandas as pd
import pytest

from strategy import RSIStrategy, SMAStrategy


def _make_df(closes: list[float]) -> pd.DataFrame:
    """Return a minimal DataFrame with a ``close`` column."""
    return pd.DataFrame({"close": closes})


class TestSMAStrategy:
    def test_hold_when_not_enough_data(self):
        strategy = SMAStrategy(short_period=5, long_period=10)
        df = _make_df([100.0] * 9)
        assert strategy.generate_signal(df) == "HOLD"

    def test_hold_when_no_crossover(self):
        strategy = SMAStrategy(short_period=3, long_period=5)
        closes = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        df = _make_df(closes)
        # Prices steadily increasing → short SMA always above long SMA, no fresh cross
        assert strategy.generate_signal(df) == "HOLD"

    def test_buy_signal_on_crossover(self):
        strategy = SMAStrategy(short_period=3, long_period=5)
        # Prices decline then spike: at the last candle short SMA (11) crosses
        # above long SMA (10), triggering a BUY.
        closes = [10, 9, 8, 7, 6, 20]
        df = _make_df(closes)
        assert strategy.generate_signal(df) == "BUY"

    def test_sell_signal_on_crossover(self):
        strategy = SMAStrategy(short_period=3, long_period=5)
        # Prices rise then collapse: at the last candle short SMA (9.33) crosses
        # below long SMA (10.2), triggering a SELL.
        closes = [10, 11, 12, 13, 14, 1]
        df = _make_df(closes)
        assert strategy.generate_signal(df) == "SELL"

    def test_invalid_periods_raise(self):
        with pytest.raises(ValueError):
            SMAStrategy(short_period=10, long_period=5)


class TestRSIStrategy:
    def test_hold_when_not_enough_data(self):
        strategy = RSIStrategy(period=14)
        df = _make_df([100.0] * 10)
        assert strategy.generate_signal(df) == "HOLD"

    def test_hold_signal(self):
        strategy = RSIStrategy(period=5, oversold_threshold=30, overbought_threshold=70)
        # Flat prices → RSI stays near 50
        df = _make_df([100.0] * 20)
        assert strategy.generate_signal(df) == "HOLD"

    def test_buy_signal_from_oversold(self):
        strategy = RSIStrategy(period=5, oversold_threshold=30, overbought_threshold=70)
        # Continuous decline drives RSI to 0 (deep oversold), then a sharp
        # recovery candle pushes RSI well above the oversold threshold → BUY.
        closes = [100, 80, 60, 50, 45, 42, 40, 39, 38, 37, 36, 35, 45]
        df = _make_df(closes)
        assert strategy.generate_signal(df) == "BUY"

    def test_invalid_thresholds_raise(self):
        with pytest.raises(ValueError):
            RSIStrategy(oversold_threshold=70, overbought_threshold=30)
