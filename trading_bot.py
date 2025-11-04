import yfinance as yf
import pandas as pd
import asyncio
import telegram
import os
import argparse
import pytz
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

# --- Data Fetching ---
def get_pdh_pdl(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="2d")
    if len(hist) < 2: return None, None
    return hist.iloc[-2]['High'], hist.iloc[-2]['Low']

def get_pwh_pwl(ticker):
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_last_week = start_week - timedelta(days=1)
    start_last_week = end_last_week - timedelta(days=6)
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_last_week, end=end_last_week)
    if hist.empty: return None, None
    return hist['High'].max(), hist['Low'].min()

def get_current_price(ticker):
    stock = yf.Ticker(ticker)
    price = stock.fast_info.get('last_price') or stock.info.get('regularMarketPrice')
    if not price:
        hist = stock.history(period="1d")
        if not hist.empty: price = hist['Close'].iloc[-1]
    return price

# --- Ticker State Management ---
class TickerState:
    def __init__(self, ticker, suffix):
        self.full_ticker = f"{ticker}{suffix}"
        self.levels = {}
        self.alert_flags = {}

    async def update_levels(self):
        pdh, pdl = get_pdh_pdl(self.full_ticker)
        pwh, pwl = get_pwh_pwl(self.full_ticker)

        if not all([pdh, pdl, pwh, pwl]):
            await send_telegram_alert(f"Could not retrieve key levels for {self.full_ticker}.")
            return False

        self.levels = {'pdh': pdh, 'pdl': pdl, 'pwh': pwh, 'pwl': pwl}
        self.alert_flags = {f"alerted_{k}": False for k in self.levels}

        await send_telegram_alert(
            f"Updated key levels for {self.full_ticker}:\n"
            f"PDH: {round(pdh, 2)}, PDL: {round(pdl, 2)}\n"
            f"PWH: {round(pwh, 2)}, PWL: {round(pwl, 2)}"
        )
        return True

    async def check_price(self):
        current_price = get_current_price(self.full_ticker)
        if current_price is None: return

        print(f"Current price for {self.full_ticker}: {round(current_price, 2)}")

        for name, val in self.levels.items():
            flag = f"alerted_{name}"
            crossed_above = 'h' in name and current_price > val and not self.alert_flags[flag]
            crossed_below = 'l' in name and current_price < val and not self.alert_flags[flag]

            if crossed_above or crossed_below:
                direction = "above" if crossed_above else "below"
                await send_telegram_alert(f"Alert: {self.full_ticker} crossed {direction} {name.upper()}! Price: {round(current_price, 2)}")
                self.alert_flags[flag] = True

            elif 'h' in name and current_price < val: self.alert_flags[flag] = False
            elif 'l' in name and current_price > val: self.alert_flags[flag] = False

# --- Main Execution ---
async def daily_updater(states, market_open_time, tz):
    while True:
        now = datetime.now(tz)
        market_open = now.replace(hour=market_open_time.hour, minute=market_open_time.minute, second=0, microsecond=0)
        wait_seconds = (market_open - now).total_seconds()
        if wait_seconds < 0: wait_seconds += 86400

        print(f"Waiting {wait_seconds / 3600:.2f} hours for the next market open.")
        await asyncio.sleep(wait_seconds)

        await asyncio.gather(*(s.update_levels() for s in states))

async def price_checker(states):
    while True:
        await asyncio.gather(*(s.check_price() for s in states))
        await asyncio.sleep(60)

async def main(args):
    await send_telegram_alert(f"Bot started for tickers: {', '.join(args.tickers)}.")

    states = [TickerState(t, args.suffix) for t in args.tickers]
    await asyncio.gather(*(s.update_levels() for s in states))

    market_tz = pytz.timezone(args.timezone)
    market_open_time = datetime.strptime(args.market_open, '%H:%M').time()

    updater_task = asyncio.create_task(daily_updater(states, market_open_time, market_tz))
    checker_task = asyncio.create_task(price_checker(states))

    await asyncio.gather(updater_task, checker_task)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in a .env file.")
    else:
        parser = argparse.ArgumentParser(description="Autonomous multi-stock trading bot.")
        parser.add_argument('--tickers', nargs='+', default=['AAPL'], help='List of stock tickers.')
        parser.add_argument('--suffix', default='', help='Exchange suffix.')
        parser.add_argument('--market-open', default='09:15', help='Market open time (HH:MM).')
        parser.add_argument('--timezone', default='Asia/Kolkata', help='Market timezone.')
        args = parser.parse_args()

        try:
            asyncio.run(main(args))
        except KeyboardInterrupt:
            print("Bot stopped by user.")
