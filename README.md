# Fully Autonomous Multi-Stock Trading Bot with Telegram Alerts

This project is a fully autonomous trading bot that monitors multiple stocks in parallel against key historical levels: the previous day's high (PDH) and low (PDL), and the previous week's high (PWH) and low (PWL). The bot runs continuously and automatically recalculates these levels for each stock at the start of each trading day. When the current price of a monitored stock crosses any of these levels, it sends an alert to a designated Telegram chat.

## Features

- **Multi-Stock Monitoring:** Track a whole watchlist of stocks in parallel.
- **Fully Autonomous:** Runs continuously and automatically recalculates key levels daily.
- **Multi-Level Strategy:** Uses both daily and weekly historical data (PDH, PDL, PWH, PWL).
- **Configurable Market Timings:** Adaptable to any stock market with configurable open times and timezones.
- **Real-Time Price Monitoring:** Utilizes the `yfinance` library for live stock data.
- **Telegram Alerts:** Sends instant, specific notifications when a stock crosses a key level.
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
The bot is pre-configured for the Indian market. To monitor multiple stocks on the NSE, use the `.NS` suffix.
```bash
# Monitor TATACAP and RELIANCE on the NSE
python trading_bot.py --tickers TATACAP RELIANCE --suffix .NS
```

**For Other Markets (e.g., US Market):**
You can configure the bot for any market by specifying the market open time and timezone.
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
