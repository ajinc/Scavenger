# Fully Autonomous Trading Bot with Telegram Alerts

This project is a fully autonomous trading bot that monitors a stock's price against key historical levels: the previous day's high (PDH) and low (PDL), and the previous week's high (PWH) and low (PWL). The bot runs continuously and automatically recalculates these levels at the start of each trading day. When the current price of a specified stock crosses any of these levels, it sends an alert to a designated Telegram chat.

## Features

- **Fully Autonomous:** The bot runs continuously and automatically recalculates key levels every day at the specified market open time.
- **Multi-Level Strategy:** Implements a trading strategy based on both daily and weekly historical data (PDH, PDL, PWH, PWL).
- **Configurable Market Timings:** Allows you to set the market open time and timezone, making it adaptable to any stock market in the world.
- **Real-Time Price Monitoring:** Utilizes the `yfinance` library to fetch live stock data.
- **Telegram Alerts:** Sends instant notifications to a Telegram chat when a trading signal is generated.
- **Global Stock Support:** Allows you to monitor stocks on international exchanges by specifying a market suffix.
- **Flexible Stock Selection:** Allows you to specify the stock ticker to monitor via a command-line argument.
- **Secure Configuration:** Manages sensitive information like API tokens using a `.env` file.
- **Tested:** Includes a suite of unit tests to verify the core logic of the application.

## Prerequisites

- Python 3.6 or higher
- A Telegram account
- A Telegram Bot Token from [BotFather](https://t.me/botfather).
- Your Telegram Chat ID from `@userinfobot`.

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
The bot is pre-configured for the Indian market (NSE/BSE). To monitor a stock on the NSE, use the `.NS` suffix.
```bash
# Monitor TATACAP on the NSE
python trading_bot.py --ticker TATACAP --suffix .NS
```

**For Other Markets (e.g., US Market):**
You can configure the bot for any market by specifying the market open time and timezone.
```bash
# Monitor TSLA on the NASDAQ (market opens at 09:30 in New York)
python trading_bot.py --ticker TSLA --market-open 09:30 --timezone America/New_York
```
You can find a list of timezones [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). For international stocks, you can find the correct ticker and suffix on [Yahoo Finance](https://finance.yahoo.com/).

## Testing

To run the unit tests, use the following command:
```bash
python -m unittest test_trading_bot.py
```
This will execute the test suite and verify that the core components of the bot are functioning correctly.
