# Binance Crypto Trading Bot

A lightweight Python trading bot that connects to the [Binance](https://www.binance.com/) exchange and automatically executes market orders based on configurable technical-analysis strategies.

## Features

- **SMA Crossover strategy** – generates BUY/SELL signals when the fast moving average crosses the slow moving average.
- **RSI strategy** – generates BUY/SELL signals based on Relative Strength Index overbought / oversold levels.
- **Dry-run mode** (default) – simulates trades without placing real orders, safe to run without real API keys.
- **Live trading mode** – places real market orders on Binance when valid API credentials are provided.
- Configurable trading pair, candle interval, and order quantity via environment variables.

## Project structure

```
.
├── bot.py            # Main BinanceBot class and entry-point
├── config.py         # Configuration (reads from environment / .env)
├── strategy.py       # SMAStrategy and RSIStrategy
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment variable file
└── tests/
    ├── test_bot.py       # Unit tests for BinanceBot and Config
    └── test_strategy.py  # Unit tests for trading strategies
```

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

| Variable | Default | Description |
|---|---|---|
| `BINANCE_API_KEY` | *(empty)* | Binance API key (required for live trading) |
| `BINANCE_API_SECRET` | *(empty)* | Binance API secret (required for live trading) |
| `TRADING_SYMBOL` | `BTCUSDT` | Trading pair symbol |
| `TRADING_INTERVAL` | `1h` | Candle interval (`1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`) |
| `TRADE_QUANTITY` | `0.001` | Order quantity in base asset |
| `DRY_RUN` | `true` | Set to `false` to place real orders |

### 3. Run the bot

```bash
# Dry-run (no real orders):
python bot.py

# Live trading (set DRY_RUN=false in .env and provide API keys):
DRY_RUN=false python bot.py
```

### 4. Run tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Using a custom strategy

Pass any `BaseStrategy` subclass to `BinanceBot`:

```python
from bot import BinanceBot
from config import Config
from strategy import RSIStrategy

bot = BinanceBot(
    config=Config(),
    strategy=RSIStrategy(period=14, oversold_threshold=30, overbought_threshold=70),
)
bot.run()
```

## Security note

Never commit your `.env` file or hard-code API keys in source code. Use environment variables or a secrets manager. It is also recommended to restrict your Binance API key to **spot trading only** and whitelist your IP address in the Binance dashboard.
