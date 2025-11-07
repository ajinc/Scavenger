# Universal Intraday Trading Bot with Dhan API Integration

This is a fully autonomous trading bot designed for intraday trading, now powered by the Dhan API for high-quality, real-time data. It features two powerful, selectable strategies: a **universal** system for comprehensive level monitoring, and a specialized **Opening Range Breakout (ORB)** strategy for intraday price action.

## Key Features

- **Dhan API Integration:** Uses the official Dhan API for reliable, real-time, and historical data.
- **Pluggable Strategies:** Choose the best strategy for your needs:
    - `universal` (Default): Monitors all key levels in parallel (PDH/PDL, PWH/PWL, and major swing points).
    - `orb`: A specialized strategy for trading opening range breakouts.
- **VWAP Confirmation:** All alerts are filtered using the VWAP for higher-quality signals.
- **Multi-Stock Monitoring:** Track an entire watchlist of stocks or indices in parallel.
- **Fully Autonomous:** Runs continuously.
- **Telegram Alerts:** Sends instant, detailed notifications to your Telegram.
- **Tested:** Includes a suite of unit tests.

## Prerequisites

- Python 3.6+
- A Telegram account & credentials.
- A DhanHQ account with API credentials.

## Setup & Configuration

1.  **Clone & Install:** `git clone <repository-url>` and `pip install -r requirements.txt`
2.  **Configure Credentials:** Copy `.env.example` to `.env` and add your Telegram and Dhan API credentials.
    - `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`: Your Telegram bot credentials.
    - `DHAN_CLIENT_ID` and `DHAN_ACCESS_TOKEN`: Your Dhan API credentials. You can generate these from your DhanHQ account dashboard.

## Usage

The bot is designed to be run from the command line and left running.

### **Universal Strategy (Default)**

This is the recommended strategy for a comprehensive market overview.

**To monitor Reliance and NIFTY:**
```bash
# Tickers should now match the Dhan security IDs
python trading_bot.py --tickers RELIANCE.NS ^NSEI
```
The bot will immediately send a summary of all the key levels it's monitoring.

### **ORB Strategy for Intraday Trading**

This is a specialized strategy for trading breakouts of the opening range.

**To monitor Reliance and NIFTY with a 15-minute opening range:**
```bash
python trading_bot.py --strategy orb --tickers RELIANCE.NS ^NSEI --orb-minutes 15
```

## Testing

Run the unit tests with:
```bash
python -m unittest test_trading_bot.py
```
