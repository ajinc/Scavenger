# Universal Intraday Trading Bot with ORB Strategy

This is a fully autonomous trading bot designed for intraday trading. It features two powerful, selectable strategies: a **universal** system for comprehensive level monitoring, and a specialized **Opening Range Breakout (ORB)** strategy for intraday price action.

## Key Features

- **Pluggable Strategies:** Choose the best strategy for your needs:
    - `universal` (Default): Monitors all key levels in parallel (PDH/PDL, PWH/PWL, and major swing points).
    - `orb`: A specialized strategy for trading opening range breakouts.
- **VWAP Confirmation:** All alerts are filtered using the VWAP for higher-quality signals.
- **Multi-Stock Monitoring:** Track an entire watchlist of stocks or indices in parallel.
- **Fully Autonomous:** Runs continuously.
- **Configurable for Any Market:** Adaptable to any global market.
- **Telegram Alerts:** Sends instant, detailed notifications to your Telegram.
- **Tested:** Includes a suite of unit tests.

## Prerequisites

- Python 3.6+
- A Telegram account & credentials.

## Setup & Configuration

1.  **Clone & Install:** `git clone <repository-url>` and `pip install -r requirements.txt`
2.  **Configure Credentials:** Copy `.env.example` to `.env` and add your Telegram Bot Token and Chat ID.

## Usage

The bot is designed to be run from the command line and left running.

### **Universal Strategy (Default)**

This is the recommended strategy for a comprehensive market overview.

**To monitor NIFTY and BANKNIFTY:**
```bash
# NIFTY: ^NSEI, BANKNIFTY: ^NSEBANK
python trading_bot.py --tickers ^NSEI ^NSEBANK
```
The bot will immediately send a summary of all the key levels it's monitoring.

### **ORB Strategy for Intraday Trading**

This is a specialized strategy for trading breakouts of the opening range.

**To monitor NIFTY and BANKNIFTY with a 15-minute opening range:**
```bash
python trading_bot.py --strategy orb --tickers ^NSEI ^NSEBANK --orb-minutes 15
```

### **Configuration for Other Markets**

Both strategies can be adapted for any market.

**Example for the US Market (ORB):**
```bash
python trading_bot.py --strategy orb --tickers TSLA AAPL --market-open 09:30 --timezone America/New_York
```

## Testing

Run the unit tests with:
```bash
python -m unittest test_trading_bot.py
```
