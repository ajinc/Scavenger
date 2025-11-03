# PDH/PDL Trading Bot with Telegram Alerts

This project is a simple yet effective trading bot that monitors a stock's price based on the previous day's high (PDH) and low (PDL). When the current price of a specified stock crosses either of these key levels, the bot sends an alert to a designated Telegram chat.

## Features

- **Real-Time Price Monitoring:** Utilizes the `yfinance` library to fetch live stock data.
- **PDH/PDL Strategy:** Implements a trading strategy based on the previous day's high and low.
- **Telegram Alerts:** Sends instant notifications to a Telegram chat when a trading signal is generated.
- **Global Stock Support:** Allows you to monitor stocks on international exchanges by specifying a market suffix.
- **Flexible Stock Selection:** Allows you to specify the stock ticker to monitor via a command-line argument.
- **Secure Configuration:** Manages sensitive information like API tokens using a `.env` file, ensuring they are not hardcoded in the source code.
- **Tested:** Includes a suite of unit tests to verify the core logic of the application.

## Prerequisites

Before you begin, ensure you have the following:

- Python 3.6 or higher
- A Telegram account
- A Telegram Bot Token. You can get one by talking to the [BotFather](https://t.me/botfather) on Telegram.
- Your Telegram Chat ID. You can get this by talking to the `@userinfobot` on Telegram.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

This project uses a `.env` file to handle sensitive information like your Telegram Bot Token and Chat ID.

1.  **Create a `.env` file:**

    Copy the example file:
    ```bash
    cp .env.example .env
    ```

2.  **Add your credentials:**

    Open the `.env` file and replace the placeholder values with your actual credentials:
    ```
    TELEGRAM_BOT_TOKEN="your-bot-token"
    TELEGRAM_CHAT_ID="your-chat-id"
    ```

## Usage

To start the trading bot, run the following command. You can use the `--ticker` and `--suffix` arguments to specify the stock and its market.

**Default (AAPL on NASDAQ):**
```bash
python trading_bot.py
```

**Specify a US Ticker (e.g., TSLA):**
```bash
python trading_bot.py --ticker TSLA
```

**Specify an Indian Ticker (e.g., TATACAP on NSE):**
```bash
python trading_bot.py --ticker TATACAP --suffix .NS
```

For stocks on other international exchanges, you will need to find the correct suffix. You can look up tickers and their suffixes on [Yahoo Finance](https://finance.yahoo.com/).

The bot will start monitoring the specified stock and send alerts to your Telegram chat when the price crosses the PDH or PDL.

## Testing

To run the unit tests, use the following command:

```bash
python -m unittest test_trading_bot.py
```

This will execute the test suite and verify that the core components of the bot are functioning correctly.
