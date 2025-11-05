# Universal Intraday Trading Bot

This is a fully autonomous trading bot designed for intraday trading. Its default strategy is a **universal** system that monitors a comprehensive set of key price levels, making it a powerful tool for identifying potential breakouts.

## Key Features

- **Universal Strategy (Default):** The bot's primary strategy monitors all of the following levels in parallel:
    - **Previous Day's High & Low (PDH/PDL)**
    - **Previous Week's High & Low (PWH/PWL)**
    - **Major Swing Highs & Lows** (from the last 6 months)
- **VWAP Confirmation:** All alerts are filtered using the Volume Weighted Average Price (VWAP) to provide higher-quality, volume-confirmed signals.
- **Multi-Stock Monitoring:** Track an entire watchlist of stocks or indices in parallel.
- **Fully Autonomous:** The bot runs continuously and is designed to be a "set it and forget it" tool.
- **Configurable for Any Market:** While pre-configured for the Indian markets, it can be adapted to any global market.
- **Telegram Alerts:** Sends instant, detailed notifications to your Telegram.
- **Tested:** Includes a suite of unit tests.

## Prerequisites

- Python 3.6+
- A Telegram account & credentials.

## Setup & Configuration

1.  **Clone & Install:**
    ```bash
    git clone <repository-url>
    pip install -r requirements.txt
    ```
2.  **Configure Credentials:**
    - Copy the example `.env` file: `cp .env.example .env`
    - Add your Telegram Bot Token and Chat ID to the `.env` file.

## Usage

The bot is designed to be run from the command line and left running.

### **Universal Strategy (Default)**

This is the recommended strategy for most use cases. It provides a comprehensive view of the market's key levels.

**To monitor NIFTY and BANKNIFTY:**
```bash
# NIFTY: ^NSEI, BANKNIFTY: ^NSEBANK
python trading_bot.py --tickers ^NSEI ^NSEBANK
```
On startup, the bot will immediately send you a summary of all the key levels it is monitoring for each index.

### **Configuration for Other Markets**

You can easily adapt the bot for any market.

**Example for the US Market:**
```bash
# Monitor TSLA and AAPL on the NASDAQ
python trading_bot.py --tickers TSLA AAPL
```

## Testing

Run the unit tests with:
```bash
python -m unittest test_trading_bot.py
```
