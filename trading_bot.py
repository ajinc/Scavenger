import yfinance as yf
import pandas as pd
import asyncio
import aioschedule
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

# --- Global State ---
key_levels = {}

# --- Helper Functions ---
def get_utc_time(local_time_str, timezone_str):
    """Converts a local time string to UTC."""
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(local_time_str, '%H:%M').time()
    today = date.today()
    local_dt = local_tz.localize(datetime.combine(today, local_time))
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.strftime('%H:%M')

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
    prev_day = hist.iloc[-2]
    return prev_day['High'], prev_day['Low']

def get_previous_week_start_end():
    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    end_last_week = start_week - timedelta(days=1)
    start_last_week = end_last_week - timedelta(days=6)
    return start_last_week, end_last_week

def get_pwh_pwl(ticker):
    stock = yf.Ticker(ticker)
    start, end = get_previous_week_start_end()
    hist = stock.history(start=start, end=end)
    if hist.empty: return None, None
    return hist['High'].max(), hist['Low'].min()

def get_current_price(ticker):
    stock = yf.Ticker(ticker)
    price = stock.fast_info.get('last_price') or stock.info.get('regularMarketPrice')
    if not price:
        hist = stock.history(period="1d")
        if not hist.empty: price = hist['Close'].iloc[-1]
    return price

# --- Core Logic ---
async def update_key_levels(ticker, suffix):
    full_ticker = f"{ticker}{suffix}"
    pdh, pdl = get_pdh_pdl(full_ticker)
    pwh, pwl = get_pwh_pwl(full_ticker)

    if not all([pdh, pdl, pwh, pwl]):
        await send_telegram_alert(f"Could not retrieve key levels for {full_ticker}.")
        return

    key_levels.update({
        'pdh': pdh, 'pdl': pdl, 'pwh': pwh, 'pwl': pwl,
        'alerted_pdh': False, 'alerted_pdl': False, 'alerted_pwh': False, 'alerted_pwl': False
    })

    await send_telegram_alert(
        f"Updated key levels for {full_ticker}:\n"
        f"PDH: {round(pdh, 2)}, PDL: {round(pdl, 2)}\n"
        f"PWH: {round(pwh, 2)}, PWL: {round(pwl, 2)}"
    )

async def check_price(ticker, suffix):
    full_ticker = f"{ticker}{suffix}"
    current_price = get_current_price(full_ticker)

    if current_price is None or not key_levels:
        return

    print(f"Current price for {full_ticker}: {round(current_price, 2)}")

    for level_name in ['pdh', 'pdl', 'pwh', 'pwl']:
        level_val = key_levels[level_name]
        alert_flag = f"alerted_{level_name}"

        crossed_above = 'h' in level_name and current_price > level_val and not key_levels[alert_flag]
        crossed_below = 'l' in level_name and current_price < level_val and not key_levels[alert_flag]

        if crossed_above or crossed_below:
            direction = "above" if crossed_above else "below"
            await send_telegram_alert(f"Alert: {full_ticker} crossed {direction} {level_name.upper()}! Price: {round(current_price, 2)}")
            key_levels[alert_flag] = True

        elif 'h' in level_name and current_price < level_val: key_levels[alert_flag] = False
        elif 'l' in level_name and current_price > level_val: key_levels[alert_flag] = False

# --- Main Execution ---
async def main(args):
    await send_telegram_alert(f"Bot started for {args.ticker}{args.suffix}.")
    await update_key_levels(args.ticker, args.suffix)

    # Schedule jobs
    utc_market_open = get_utc_time(args.market_open, args.timezone)
    aioschedule.every().day.at(utc_market_open).do(update_key_levels, args.ticker, args.suffix)
    aioschedule.every(1).minutes.do(check_price, args.ticker, args.suffix)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in a .env file.")
    else:
        parser = argparse.ArgumentParser(description="Autonomous trading bot.")
        parser.add_argument('--ticker', default='AAPL', help='Stock ticker (e.g., AAPL, TATACAP).')
        parser.add_argument('--suffix', default='', help='Exchange suffix (e.g., .NS for NSE).')
        parser.add_argument('--market-open', default='09:15', help='Market open time (HH:MM).')
        parser.add_argument('--timezone', default='Asia/Kolkata', help='Market timezone.')
        args = parser.parse_args()

        try:
            asyncio.run(main(args))
        except KeyboardInterrupt:
            print("Bot stopped by user.")
