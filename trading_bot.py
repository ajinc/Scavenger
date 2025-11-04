import yfinance as yf
import pandas as pd
import asyncio
import telegram
import os
import argparse
import pytz
from dotenv import load_dotenv
from datetime import date, timedelta, datetime, time

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

# --- Data Fetching ---
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

# --- Strategy Base Class ---
class Strategy:
    def __init__(self, ticker_state, args):
        self.ts = ticker_state
        self.args = args

    async def update_levels(self):
        raise NotImplementedError

    async def check_price(self):
        raise NotImplementedError

# --- Levels Strategy ---
class LevelsStrategy(Strategy):
    async def update_levels(self):
        pdh, pdl = self._get_pdh_pdl()
        pwh, pwl = self._get_pwh_pwl()

        if not all([pdh, pdl, pwh, pwl]):
            await send_telegram_alert(f"Could not retrieve key levels for {self.ts.full_ticker}.")
            return False

        self.ts.levels = {'pdh': pdh, 'pdl': pdl, 'pwh': pwh, 'pwl': pwl}
        self.ts.alert_flags = {f"alerted_{k}": False for k in self.ts.levels}

        await send_telegram_alert(
            f"Updated levels for {self.ts.full_ticker}:\n"
            f"PDH: {round(pdh, 2)}, PDL: {round(pdl, 2)}\n"
            f"PWH: {round(pwh, 2)}, PWL: {round(pwl, 2)}"
        )
        return True

    async def check_price(self):
        price = get_current_price(self.ts.full_ticker)
        vwap = get_vwap(self.ts.full_ticker)

        if price is None or vwap is None: return

        for name, val in self.ts.levels.items():
            flag = f"alerted_{name}"
            above = 'h' in name and price > val and not self.ts.alert_flags[flag] and price > vwap
            below = 'l' in name and price < val and not self.ts.alert_flags[flag] and price < vwap

            if above or below:
                direction = "above" if above else "below"
                await send_telegram_alert(
                    f"Alert: {self.ts.full_ticker} crossed {direction} {name.upper()} with VWAP confirmation!\n"
                    f"Price: {round(price, 2)}, VWAP: {round(vwap, 2)}"
                )
                self.ts.alert_flags[flag] = True

            elif 'h' in name and price < val: self.ts.alert_flags[flag] = False
            elif 'l' in name and price > val: self.ts.alert_flags[flag] = False

    def _get_pdh_pdl(self):
        hist = yf.Ticker(self.ts.full_ticker).history(period="2d")
        if len(hist) < 2: return None, None
        return hist.iloc[-2]['High'], hist.iloc[-2]['Low']

    def _get_pwh_pwl(self):
        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        end_last_week = start_week - timedelta(days=1)
        start_last_week = end_last_week - timedelta(days=6)
        hist = yf.Ticker(self.ts.full_ticker).history(start=start_last_week, end=end_last_week)
        if hist.empty: return None, None
        return hist['High'].max(), hist['Low'].min()

# --- ORB Strategy ---
class OrbStrategy(Strategy):
    async def update_levels(self):
        """Calculates the opening range high and low."""
        tz = pytz.timezone(self.args.timezone)
        market_open = datetime.strptime(self.args.market_open, '%H:%M').time()

        # Wait until the opening range period has passed
        now = datetime.now(tz).time()
        orb_end_time = (datetime.combine(date.today(), market_open) + timedelta(minutes=self.args.orb_minutes)).time()

        if now < orb_end_time:
            wait_seconds = (datetime.combine(date.today(), orb_end_time) - datetime.combine(date.today(), now)).total_seconds()
            print(f"Waiting {wait_seconds / 60:.2f} minutes for opening range to form.")
            await asyncio.sleep(wait_seconds)

        # Fetch intraday data for the opening range
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

        # Breakout above ORB High
        if price > orb_high and not self.ts.alert_flags['alerted_orb_high'] and price > vwap:
            await send_telegram_alert(
                f"Alert: {self.ts.full_ticker} broke above opening range with VWAP confirmation!\n"
                f"Price: {round(price, 2)}, VWAP: {round(vwap, 2)}"
            )
            self.ts.alert_flags['alerted_orb_high'] = True

        # Breakout below ORB Low
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
async def daily_updater(states, market_open_time, tz):
    while True:
        now = datetime.now(tz)
        market_open = now.replace(hour=market_open_time.hour, minute=market_open_time.minute, second=0)
        wait = (market_open - now).total_seconds()
        if wait < 0: wait += 86400
        await asyncio.sleep(wait)
        await asyncio.gather(*(s.strategy.update_levels() for s in states))

async def price_checker(states):
    while True:
        await asyncio.gather(*(s.strategy.check_price() for s in states))
        await asyncio.sleep(60)

async def main(args):
    strategy_map = {"levels": LevelsStrategy, "orb": OrbStrategy}
    strategy_class = strategy_map.get(args.strategy)
    if not strategy_class:
        print(f"Unknown strategy: {args.strategy}")
        return

    await send_telegram_alert(f"Bot starting with '{args.strategy}' strategy for: {', '.join(args.tickers)}.")

    states = [TickerState(t, args.suffix, strategy_class, args) for t in args.tickers]
    await asyncio.gather(*(s.strategy.update_levels() for s in states))

    market_tz = pytz.timezone(args.timezone)
    market_open_time = datetime.strptime(args.market_open, '%H:%M').time()

    await asyncio.gather(
        daily_updater(states, market_open_time, market_tz),
        price_checker(states)
    )

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Missing Telegram credentials in .env file.")
    else:
        parser = argparse.ArgumentParser(description="A multi-strategy, multi-stock trading bot.")
        parser.add_argument('--strategy', default='levels', choices=['levels', 'orb'], help='The trading strategy to use.')
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
