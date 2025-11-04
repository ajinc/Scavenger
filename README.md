# Intraday Price Action Bot for Indian Markets

This is a fully autonomous trading bot designed for intraday price action strategies, with a special focus on the Indian markets (NIFTY & BANKNIFTY). It supports multiple strategies, provides VWAP confirmation for all its alerts, and now identifies major long-term support and resistance levels.

## Features

- **Swing Level Analysis:** On startup, the bot automatically identifies and displays the major swing highs and lows from the last six months, giving you immediate insight into the long-term market structure.
- **Pluggable Strategies:** Choose between different trading strategies. Currently supports:
    - `orb`: Opening Range Breakout (perfect for indices like NIFTY).
    - `levels`: The classic PDH/PDL and PWH/PWL strategy.
- **VWAP Confirmation:** All alerts are filtered using the VWAP for higher-quality signals.
- **Multi-Stock Monitoring:** Track multiple stocks or indices in parallel.
- **Fully Autonomous:** Runs continuously and recalculates levels at the start of each trading day.
- **Configurable for Any Market:** While pre-configured for India, you can adapt it to any market.
- **Real-Time Data:** Uses `yfinance` for live price data.
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

### **For Indian Markets: ORB Strategy (Recommended)**

This is the recommended strategy for intraday trading on indices like NIFTY (`^NSEI`) and BANKNIFTY (`^NSEBANK`).

**To monitor NIFTY and BANKNIFTY with a 15-minute opening range:**
```bash
python trading_bot.py --strategy orb --tickers ^NSEI ^NSEBANK --orb-minutes 15
```
On startup, the bot will first send you the major swing levels for NIFTY and BANKNIFTY. It will then begin monitoring for opening range breakouts.

### **Using the Classic Levels Strategy**

You can still use the original PDH/PDL and PWH/PWL strategy if you prefer.

**To monitor a stock on the NSE with the levels strategy:**
```bash
python trading_bot.py --strategy levels --tickers TATACAP --suffix .NS
```

### **Configuration for Other Markets**

You can adapt the bot for any market by specifying the market open time and timezone.

**Example for the US Market (ORB Strategy):**
```bash
python trading_bot.py --strategy orb --tickers TSLA AAPL --market-open 09:30 --timezone America/New_York --orb-minutes 30
```

## Testing

Run the unit tests with:
```bash
python -m unittest test_trading_bot.py
```
