"""Trading strategies for the Binance bot.

Each strategy receives a :class:`pandas.DataFrame` of OHLCV data and returns
a signal string: ``"BUY"``, ``"SELL"``, or ``"HOLD"``.
"""

from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    """Abstract base class that all strategies must implement."""

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> str:
        """Return ``"BUY"``, ``"SELL"``, or ``"HOLD"`` based on *df*."""


class SMAStrategy(BaseStrategy):
    """Simple Moving-Average (SMA) crossover strategy.

    A **BUY** signal is generated when the short-period SMA crosses above
    the long-period SMA.  A **SELL** signal is generated when it crosses
    below.  Otherwise the signal is **HOLD**.

    Parameters
    ----------
    short_period:
        Number of candles for the fast SMA (default 9).
    long_period:
        Number of candles for the slow SMA (default 21).
    """

    def __init__(self, short_period: int = 9, long_period: int = 21) -> None:
        if short_period >= long_period:
            raise ValueError("short_period must be less than long_period")
        self.short_period = short_period
        self.long_period = long_period

    def generate_signal(self, df: pd.DataFrame) -> str:
        if len(df) < self.long_period + 1:
            return "HOLD"

        close = df["close"].astype(float)
        short_sma = close.rolling(self.short_period).mean()
        long_sma = close.rolling(self.long_period).mean()

        prev_short = short_sma.iloc[-2]
        prev_long = long_sma.iloc[-2]
        curr_short = short_sma.iloc[-1]
        curr_long = long_sma.iloc[-1]

        if prev_short <= prev_long and curr_short > curr_long:
            return "BUY"
        if prev_short >= prev_long and curr_short < curr_long:
            return "SELL"
        return "HOLD"


class RSIStrategy(BaseStrategy):
    """Relative Strength Index (RSI) strategy.

    Generates a **BUY** signal when RSI crosses above *oversold_threshold*
    from below, and a **SELL** signal when RSI crosses below
    *overbought_threshold* from above.

    Parameters
    ----------
    period:
        Look-back period for RSI calculation (default 14).
    oversold_threshold:
        RSI level below which the asset is considered oversold (default 30).
    overbought_threshold:
        RSI level above which the asset is considered overbought (default 70).
    """

    def __init__(
        self,
        period: int = 14,
        oversold_threshold: float = 30.0,
        overbought_threshold: float = 70.0,
    ) -> None:
        if oversold_threshold >= overbought_threshold:
            raise ValueError("oversold_threshold must be less than overbought_threshold")
        self.period = period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold

    def _compute_rsi(self, close: pd.Series) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=self.period - 1, min_periods=self.period).mean()
        avg_loss = loss.ewm(com=self.period - 1, min_periods=self.period).mean()
        rs = avg_gain / avg_loss.replace(0, float("inf"))
        return 100 - (100 / (1 + rs))

    def generate_signal(self, df: pd.DataFrame) -> str:
        if len(df) < self.period + 1:
            return "HOLD"

        close = df["close"].astype(float)
        rsi = self._compute_rsi(close)

        prev_rsi = rsi.iloc[-2]
        curr_rsi = rsi.iloc[-1]

        if prev_rsi <= self.oversold_threshold and curr_rsi > self.oversold_threshold:
            return "BUY"
        if prev_rsi >= self.overbought_threshold and curr_rsi < self.overbought_threshold:
            return "SELL"
        return "HOLD"
