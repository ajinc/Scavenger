# Fully Autonomous Multi-Stock Trading Bot with VWAP Confirmation

This project is a fully autonomous trading bot that monitors multiple stocks in parallel against key historical levels, now with VWAP (Volume Weighted Average Price) confirmation. The bot tracks the previous day's high (PDH) and low (PDL), and the previous week's high (PWH) and low (PWL). When the price crosses one of these key levels, it now checks if the price is also above/below the VWAP before sending an alert, leading to higher-quality signals.

## Features

- **VWAP Confirmation:** Alerts are filtered using the VWAP to provide stronger, more reliable trading signals.
- **Multi-Stock Monitoring:** Track a whole watchlist of stocks in parallel.
- **Fully Autonomous:** Runs continuously and automatically recalculates key levels daily.
- **Multi-Level Strategy:** Uses both daily and weekly historical data (PDH, PDL, PWH, PWL).
- **Configurable Market Timings:** Adaptable to any stock market with configurable open times and timezones.
- **Real-Time Price Monitoring:** Utilizes `yfinance` and `pandas-ta` for live price and indicator data.
- **Telegram Alerts:** Sends instant, detailed notifications when a stock crosses a key level with VWAP confirmation.
- **Global Stock Support:** Monitor stocks on international exchanges by specifying a market suffix.
- **Secure Configuration:** Manages API tokens using a `.env` file.
- **Tested:** Includes a suite of unit tests to verify the core logic.

## Prerequisites

- Python 3.6 or higher
- A Telegram account & credentials (Bot Token, Chat ID).

## Setup

1.  **Clone the repository:** `git clone <repository-url>`
2.  **Install dependencies:** `pip install -r requirements.txt`

## Configuration

1.  **Create a `.env` file:** `cp .env.example .env`
2.  **Add your credentials to `.env`:**
    ```
    TELEGRAM_BOT_TOKEN="your-bot-token"
    TELEGRAM_CHAT_ID="your-chat-id"
    ```

## Usage

To start the trading bot, run the following command. The bot will run continuously, so you can leave it running in a terminal or on a server.

**For the Indian Market (Default):**
```bash
# Monitor TATACAP and RELIANCE on the NSE
python trading_bot.py --tickers TATACAP RELIANCE --suffix .NS
```

**For Other Markets (e.g., US Market):**
```bash
# Monitor TSLA, AAPL, and GOOGL on the NASDAQ
python trading_bot.py --tickers TSLA AAPL GOOGL --market-open 09:30 --timezone America/New_York
```
You can find timezones [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) and international stock tickers and suffixes on [Yahoo Finance](https://finance.yahoo.com/).

## Testing

To run the unit tests, use the following command:
```bash
python -m unittest test_trading_bot.py
```
This will execute the test suite and verify that the core components of the bot are functioning correctly.
