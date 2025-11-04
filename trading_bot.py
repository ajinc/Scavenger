import yfinance as yf
import pandas as pd
import time
import telegram
import os
import argparse
import asyncio
import schedule
import pytz
from dotenv import load_dotenv
from datetime import date, timedelta, datetime

# Load environment variables from .env file
load_dotenv()

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize the bot
if TELEGRAM_BOT_TOKEN:
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
else:
    bot = None

# --- Global State for Key Levels ---
key_levels = {}

async def send_telegram_alert(message):
    """
    Sends a message to the specified Telegram chat.
    """
    if not bot or not TELEGRAM_CHAT_ID:
        print("Telegram bot not configured. Skipping alert.")
        return
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"Telegram alert sent: {message}")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def get_pdh_pdl(ticker):
    """
    Fetches the previous day's high and low for a given stock.
    """
    stock = yf.Ticker(ticker)
    hist = stock.history(period="2d")
    if len(hist) < 2:
        return None, None
    previous_day = hist.iloc[-2]
    return previous_day['High'], previous_day['Low']

def get_previous_week_start_end():
    """
    Gets the start and end dates of the previous week.
    """
    today = date.today()
    start_of_this_week = today - timedelta(days=today.weekday())
    end_of_last_week = start_of_this_week - timedelta(days=1)
    start_of_last_week = end_of_last_week - timedelta(days=6)
    return start_of_last_week, end_of_last_week

def get_pwh_pwl(ticker):
    """
    Fetches the previous week's high and low for a given stock.
    """
    stock = yf.Ticker(ticker)
    start, end = get_previous_week_start_end()
    hist = stock.history(start=start, end=end)
    if hist.empty:
        return None, None
    return hist['High'].max(), hist['Low'].min()

def get_current_price(ticker):
    """
    Fetches the current price of a given stock using multiple methods for robustness.
    """
    stock = yf.Ticker(ticker)
    price = stock.fast_info.get('last_price') or stock.info.get('regularMarketPrice')
    if not price:
        hist = stock.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
    return price

async def update_key_levels(ticker, suffix):
    """
    Recalculates and updates the key levels (PDH, PDL, PWH, PWL).
    """
    full_ticker = f"{ticker}{suffix}"
    pdh, pdl = get_pdh_pdl(full_ticker)
    pwh, pwl = get_pwh_pwl(full_ticker)

    if not all([pdh, pdl, pwh, pwl]):
        message = f"Could not retrieve key levels for {full_ticker}. Please check the ticker and suffix."
        print(message)
        await send_telegram_alert(message)
        return

    key_levels.update({
        'pdh': pdh, 'pdl': pdl, 'pwh': pwh, 'pwl': pwl,
        'alerted_pdh': False, 'alerted_pdl': False, 'alerted_pwh': False, 'alerted_pwl': False
    })

    message = (
        f"Updated key levels for {full_ticker} at market open:\n"
        f"PDH: {round(pdh, 2)}, PDL: {round(pdl, 2)}\n"
        f"PWH: {round(pwh, 2)}, PWL: {round(pwl, 2)}"
    )
    print(message)
    await send_telegram_alert(message)

async def check_strategy(ticker, suffix):
    """
    Continuously checks the price against the key levels and sends alerts.
    """
    full_ticker = f"{ticker}{suffix}"

    while True:
        # Run pending scheduled tasks
        schedule.run_pending()

        current_price = get_current_price(full_ticker)
        if current_price is None or not key_levels:
            await asyncio.sleep(60)
            continue

        print(f"Current price for {full_ticker}: {round(current_price, 2)}")

        # Check against key levels
        for level_name in ['pdh', 'pdl', 'pwh', 'pwl']:
            level_value = key_levels[level_name]
            alert_flag = f"alerted_{level_name}"

            crossed_above = level_name.endswith('h') and current_price > level_value and not key_levels[alert_flag]
            crossed_below = level_name.endswith('l') and current_price < level_value and not key_levels[alert_flag]

            if crossed_above or crossed_below:
                direction = "above" if crossed_above else "below"
                message = f"Alert: {full_ticker} crossed {direction} {level_name.upper()}! Price: {round(current_price, 2)}"
                print(message)
                await send_telegram_alert(message)
                key_levels[alert_flag] = True

            # Reset flags if price moves back
            elif level_name.endswith('h') and current_price < level_value:
                key_levels[alert_flag] = False
            elif level_name.endswith('l') and current_price > level_value:
                key_levels[alert_flag] = False

        await asyncio.sleep(60)


if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in a .env file.")
    else:
        parser = argparse.ArgumentParser(description="A trading bot that sends alerts based on key daily and weekly levels.")
        parser.add_argument('--ticker', default='AAPL', help='The stock ticker to monitor (e.g., AAPL, TATACAP).')
        parser.add_argument('--suffix', default='', help='The exchange suffix (e.g., .NS for NSE).')
        parser.add_argument('--market-open', default='09:15', help='Market open time in HH:MM format.')
        parser.add_argument('--timezone', default='Asia/Kolkata', help='The timezone for the market open time.')
        args = parser.parse_args()

        # Set the timezone
        market_timezone = pytz.timezone(args.timezone)

        # Schedule the daily recalculation of key levels
        schedule.every().day.at(args.market_open, market_timezone).do(
            lambda: asyncio.run(update_key_levels(args.ticker, args.suffix))
        )

        # Initial calculation
        asyncio.run(update_key_levels(args.ticker, args.suffix))

        # Start the main monitoring loop
        asyncio.run(check_strategy(args.ticker, args.suffix))
