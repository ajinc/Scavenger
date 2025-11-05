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
load_dotenv()

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
        hist_2d = yf.Ticker(self.ts.full_ticker).history(period="2d")
        if len(hist_2d) > 1:
            levels['pdh'], levels['pdl'] = hist_2d.iloc[-2][['High', 'Low']]
        hist_1w = yf.Ticker(self.ts.full_ticker).history(period="1w")
        if not hist_1w.empty:
            levels['pwh'], levels['pwl'] = hist_1w.iloc[0][['High', 'Low']]
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
        if price is None or vwap is None: return

        for name, val in self.ts.levels.items():
            flag = f"alerted_{name}"
            above = 'high' in name and price > val and not self.ts.alert_flags[flag] and price > vwap
            below = 'low' in name and price < val and not self.ts.alert_flags[flag] and price < vwap

            if above or below:
                direction = "above" if above else "below"
                await send_telegram_alert(
                    f"Alert: {self.ts.full_ticker} crossed {direction} {name.upper()}!\n"
                    f"Price: {round(price, 2)}, VWAP: {round(vwap, 2)}"
                )
                self.ts.alert_flags[flag] = True

            elif 'high' in name and price < val: self.ts.alert_flags[flag] = False
            elif 'low' in name and price > val: self.ts.alert_flags[flag] = False

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

class OrbStrategy(Strategy):
    async def update_levels(self):
        tz = pytz.timezone(self.args.timezone)
        market_open = datetime.strptime(self.args.market_open, '%H:%M').time()
        now = datetime.now(tz).time()
        orb_end_time = (datetime.combine(date.today(), market_open) + timedelta(minutes=self.args.orb_minutes)).time()

        if now < orb_end_time:
            wait_seconds = (datetime.combine(date.today(), orb_end_time) - datetime.combine(date.today(), now)).total_seconds()
            await asyncio.sleep(wait_seconds)

        intraday_data = yf.Ticker(self.ts.full_ticker).history(period="1d", interval="1m")
        if intraday_data.empty:
            await send_telegram_alert(f"Could not fetch intraday data for {self.ts.full_ticker}.")
            return False

        opening_range_data = intraday_data.between_time(market_open, orb_end_time)
        if opening_range_data.empty:
            await send_telegram_alert(f"No data for opening range for {self.ts.full_ticker}.")
            return False

        orb_high = opening_range_data['High'].max()
        orb_low = opening_range_data['Low'].min()

        self.ts.levels = {'orb_high': orb_high, 'orb_low': orb_low}
        self.ts.alert_flags = {f"alerted_{k}": False for k in self.ts.levels}

        await send_telegram_alert(
            f"Opening range for {self.ts.full_ticker} ({self.args.orb_minutes} mins):\n"
            f"High: {round(orb_high, 2)}, Low: {round(orb_low, 2)}"
        )
        return True

    async def check_price(self):
        price = get_current_price(self.ts.full_ticker)
        vwap = get_vwap(self.ts.full_ticker)
        if price is None or vwap is None: return

        orb_high = self.ts.levels.get('orb_high')
        orb_low = self.ts.levels.get('orb_low')
        if not all([orb_high, orb_low]): return

        if price > orb_high and not self.ts.alert_flags['alerted_orb_high'] and price > vwap:
            await send_telegram_alert(
                f"Alert: {self.ts.full_ticker} broke above opening range with VWAP confirmation!\n"
                f"Price: {round(price, 2)}, VWAP: {round(vwap, 2)}"
            )
            self.ts.alert_flags['alerted_orb_high'] = True

        elif price < orb_low and not self.ts.alert_flags['alerted_orb_low'] and price < vwap:
            await send_telegram_alert(
                f"Alert: {self.ts.full_ticker} broke below opening range with VWAP confirmation!\n"
                f"Price: {round(price, 2)}, VWAP: {round(vwap, 2)}"
            )
            self.ts.alert_flags['alerted_orb_low'] = True

# --- Ticker State ---
class TickerState:
    def __init__(self, ticker, suffix, strategy_class, args):
        self.full_ticker = f"{ticker}{suffix}"
        self.levels = {}
        self.alert_flags = {}
        self.strategy = strategy_class(self, args)

# --- Main Execution ---
async def price_checker(states):
    while True:
        await asyncio.gather(*(s.strategy.check_price() for s in states))
        await asyncio.sleep(60)

async def main(args):
    strategy_map = {"universal": UniversalStrategy, "orb": OrbStrategy}
    strategy_class = strategy_map.get(args.strategy)
    if not strategy_class:
        print(f"Unknown strategy: {args.strategy}")
        return

    await send_telegram_alert(f"Bot starting with '{args.strategy}' strategy for: {', '.join(args.tickers)}.")

    states = [TickerState(t, args.suffix, strategy_class, args) for t in args.tickers]
    await asyncio.gather(*(s.strategy.update_levels() for s in states))

    await price_checker(states)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Missing Telegram credentials in .env file.")
    else:
        parser = argparse.ArgumentParser(description="A multi-strategy, multi-stock trading bot.")
        parser.add_argument('--strategy', default='universal', choices=['universal', 'orb'], help='The trading strategy to use.')
        parser.add_argument('--tickers', nargs='+', default=['AAPL'], help='List of stock tickers.')
        parser.add_argument('--suffix', default='', help='Exchange suffix for tickers.')
        parser.add_argument('--market-open', default='09:15', help='Market open time (HH:MM).')
        parser.add_argument('--timezone', default='Asia/Kolkata', help='Timezone for the market.')
        parser.add_argument('--orb-minutes', type=int, default=15, help='Opening range breakout in minutes.')
        args = parser.parse_args()

        try:
            asyncio.run(main(args))
        except KeyboardInterrupt:
            print("Bot stopped by user.")
