import yfinance as yf
import pandas as pd
import asyncio
import telegram
import os
import argparse
import pytz
from scipy.signal import find_peaks
from dotenv import load_dotenv
from datetime import date, timedelta, datetime

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

# --- Telegram Alert ---
async def send_telegram_alert(message):
    if not bot or not TELEGRAM_CHAT_ID:
        print("Telegram bot not configured.")
        return
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"Alert sent: {message}")
    except Exception as e:
        print(f"Failed to send alert: {e}")

# --- Data Fetching & Analysis ---
def get_current_price(ticker):
    stock = yf.Ticker(ticker)
    price = stock.fast_info.get('last_price') or stock.info.get('regularMarketPrice')
    if not price:
        hist = stock.history(period="1d")
        if not hist.empty: price = hist['Close'].iloc[-1]
    return price

def get_vwap(ticker):
    stock = yf.Ticker(ticker)
    intraday_data = stock.history(period="1d", interval="1m")
    if intraday_data.empty: return None
    if 'Volume' not in intraday_data.columns or intraday_data['Volume'].sum() == 0:
        return None
    intraday_data['VWAP'] = (intraday_data['Close'] * intraday_data['Volume']).cumsum() / intraday_data['Volume'].cumsum()
    return intraday_data.iloc[-1]['VWAP']

# --- Strategy Classes ---
class Strategy:
    def __init__(self, ts, args):
        self.ts = ts
        self.args = args
    async def update_levels(self): raise NotImplementedError
    async def check_price(self): raise NotImplementedError

class UniversalStrategy(Strategy):
    async def update_levels(self):
        levels = {}
        hist_5d = yf.Ticker(self.ts.full_ticker).history(period="5d")

        if len(hist_5d) > 1:
            levels['pdh'] = hist_5d.iloc[-2]['High']
            levels['pdl'] = hist_5d.iloc[-2]['Low']

        if not hist_5d.empty:
            levels['pwh'] = hist_5d['High'].max()
            levels['pwl'] = hist_5d['Low'].min()

        swing_highs, swing_lows = self._get_swing_levels()
        for i, v in enumerate(swing_highs): levels[f'swing_high_{i}'] = v
        for i, v in enumerate(swing_lows): levels[f'swing_low_{i}'] = v

        if not levels:
            await send_telegram_alert(f"Could not retrieve any key levels for {self.ts.full_ticker}.")
            return False

        self.ts.levels = levels
        self.ts.alert_flags = {f"alerted_{k}": False for k in self.ts.levels}
        level_str = "\n".join([f"{k.upper()}: {round(v, 2)}" for k, v in self.ts.levels.items()])
        await send_telegram_alert(f"Key levels for {self.ts.full_ticker}:\n{level_str}")
        return True

    async def check_price(self):
        price = get_current_price(self.ts.full_ticker)
        vwap = get_vwap(self.ts.full_ticker)
        if price is None:
            return

        for name, val in self.ts.levels.items():
            flag = f"alerted_{name}"
            is_high_level = 'high' in name or name.endswith('h')
            is_low_level = 'low' in name or name.endswith('l')

            alert = False
            if vwap is not None:
                # Logic with VWAP confirmation
                if is_high_level and price > val and price > vwap and not self.ts.alert_flags.get(flag, False):
                    alert = True
                elif is_low_level and price < val and price < vwap and not self.ts.alert_flags.get(flag, False):
                    alert = True
            else:
                # Logic without VWAP (for indices)
                if is_high_level and price > val and not self.ts.alert_flags.get(flag, False):
                    alert = True
                elif is_low_level and price < val and not self.ts.alert_flags.get(flag, False):
                    alert = True

            if alert:
                direction = "above" if is_high_level else "below"
                vwap_str = f", VWAP: {round(vwap, 2)}" if vwap is not None else ""
                await send_telegram_alert(
                    f"Alert: {self.ts.full_ticker} crossed {direction} {name.upper()}!\n"
                    f"Price: {round(price, 2)}{vwap_str}"
                )
                self.ts.alert_flags[flag] = True
            elif is_high_level and price < val:
                self.ts.alert_flags[flag] = False
            elif is_low_level and price > val:
                self.ts.alert_flags[flag] = False

    def _get_swing_levels(self, months=6, prominence=0.1):
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        hist = yf.Ticker(self.ts.full_ticker).history(start=start_date, end=end_date)
        if hist.empty: return [], []
        price_range = hist['High'].max() - hist['Low'].min()
        required_prominence = price_range * prominence
        high_peaks, _ = find_peaks(hist['High'], prominence=required_prominence)
        low_peaks, _ = find_peaks(-hist['Low'], prominence=required_prominence)
        return hist.iloc[high_peaks]['High'].nlargest(3).tolist(), hist.iloc[low_peaks]['Low'].nsmallest(3).tolist()

# --- Ticker State ---
class TickerState:
    def __init__(self, ticker, suffix, strategy_class, args):
        self.full_ticker = f"{ticker}{suffix}"
        self.levels = {}
        self.alert_flags = {}
        self.strategy = strategy_class(self, args)

# --- Main Execution ---
async def price_checker_task(states):
    while True:
        await asyncio.gather(*(s.strategy.check_price() for s in states))
        await asyncio.sleep(60)

async def main(args):
    strategy_map = {"universal": UniversalStrategy}
    strategy_class = strategy_map.get(args.strategy)
    if not strategy_class:
        print(f"Unknown strategy: {args.strategy}")
        return

    await send_telegram_alert(f"Bot starting with '{args.strategy}' strategy for: {', '.join(args.tickers)}.")

    states = [TickerState(t, args.suffix, strategy_class, args) for t in args.tickers]
    await asyncio.gather(*(s.strategy.update_levels() for s in states))

    # Start the price checker task
    await price_checker_task(states)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Missing Telegram credentials in .env file.")
    else:
        parser = argparse.ArgumentParser(description="A multi-strategy, multi-stock trading bot.")
        parser.add_argument('--strategy', default='universal', choices=['universal'], help='The trading strategy to use.')
        parser.add_argument('--tickers', nargs='+', default=['AAPL'], help='List of stock tickers.')
        parser.add_argument('--suffix', default='', help='Exchange suffix for tickers.')
        args = parser.parse_args()

        try:
            asyncio.run(main(args))
        except KeyboardInterrupt:
            print("Bot stopped by user.")
