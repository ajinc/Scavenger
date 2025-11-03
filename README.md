# PDH/PDL Trading Bot with Telegram Alerts

This project is a simple yet effective trading bot that monitors a stock's price based on the previous day's high (PDH) and low (PDL). When the current price of a specified stock crosses either of these key levels, the bot sends an alert to a designated Telegram chat.

## Features

- **Real-Time Price Monitoring:** Utilizes the `yfinance` library to fetch live stock data.
- **PDH/PDL Strategy:** Implements a trading strategy based on the previous day's high and low.
- **Telegram Alerts:** Sends instant notifications to a Telegram chat when a trading signal is generated.
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

To start the trading bot, run the following command:

```bash
python trading_bot.py
```

The bot will start monitoring the specified stock (the default is "AAPL") and send alerts to your Telegram chat when the price crosses the PDH or PDL.

## Testing

To run the unit tests, use the following command:

```bash
python -m unittest test_trading_bot.py
```

This will execute the test suite and verify that the core components of the bot are functioning correctly.
