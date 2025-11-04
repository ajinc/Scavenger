import yfinance as yf
import pandas as pd
import time
import telegram
import os
import argparse
import asyncio
from dotenv import load_dotenv
from datetime import date, timedelta

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
    pdh = previous_day['High']
    pdl = previous_day['Low']
    return pdh, pdl

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
    pwh = hist['High'].max()
    pwl = hist['Low'].min()
    return pwh, pwl

def get_current_price(ticker):
    """
    Fetches the current price of a given stock using multiple methods for robustness.
    """
    stock = yf.Ticker(ticker)

    # Method 1: Use 'fast_info' for a quick price check
    price = stock.fast_info.get('last_price')
    if price:
        return price

    # Method 2: Use the more detailed 'info' dictionary
    price = stock.info.get('regularMarketPrice')
    if price:
        return price

    # Method 3: Fetch the most recent history and get the last close price
    hist = stock.history(period="1d")
    if not hist.empty:
        return hist['Close'].iloc[-1]

    return None


async def check_strategy(ticker, suffix):
    """
    Checks the trading strategy for a given stock.
    """
    full_ticker = f"{ticker}{suffix}"
    await send_telegram_alert(f"Trading bot started for {full_ticker}.")

    pdh, pdl = get_pdh_pdl(full_ticker)
    pwh, pwl = get_pwh_pwl(full_ticker)

    if not all([pdh, pdl, pwh, pwl]):
        message = f"Could not retrieve key levels for {full_ticker}. Please check the ticker and suffix."
        print(message)
        await send_telegram_alert(message)
        return

    message = (
        f"Key levels for {full_ticker}:\n"
        f"PDH: {round(pdh, 2)}, PDL: {round(pdl, 2)}\n"
        f"PWH: {round(pwh, 2)}, PWL: {round(pwl, 2)}"
    )
    print(message)
    await send_telegram_alert(message)

    alerted_pdh_cross = False
    alerted_pdl_cross = False
    alerted_pwh_cross = False
    alerted_pwl_cross = False

    while True:
        current_price = get_current_price(full_ticker)
        if current_price is None:
            print(f"Could not fetch current price for {full_ticker}. Skipping this iteration.")
            await asyncio.sleep(60)
            continue

        print(f"Current price for {full_ticker}: {round(current_price, 2)}")

        # Daily high/low alerts
        if current_price > pdh and not alerted_pdh_cross:
            message = f"Alert: {full_ticker} crossed above PDH! Price: {round(current_price, 2)}"
            print(message)
            await send_telegram_alert(message)
            alerted_pdh_cross = True
        elif current_price < pdh:
            alerted_pdh_cross = False

        if current_price < pdl and not alerted_pdl_cross:
            message = f"Alert: {full_ticker} crossed below PDL! Price: {round(current_price, 2)}"
            print(message)
            await send_telegram_alert(message)
            alerted_pdl_cross = True
        elif current_price > pdl:
            alerted_pdl_cross = False

        # Weekly high/low alerts
        if current_price > pwh and not alerted_pwh_cross:
            message = f"Alert: {full_ticker} crossed above PWH! Price: {round(current_price, 2)}"
            print(message)
            await send_telegram_alert(message)
            alerted_pwh_cross = True
        elif current_price < pwh:
            alerted_pwh_cross = False

        if current_price < pwl and not alerted_pwl_cross:
            message = f"Alert: {full_ticker} crossed below PWL! Price: {round(current_price, 2)}"
            print(message)
            await send_telegram_alert(message)
            alerted_pwl_cross = True
        elif current_price > pwl:
            alerted_pwl_cross = False

        await asyncio.sleep(60)


if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
        print("Please create a .env file and add your credentials there. See .env.example for reference.")
    else:
        parser = argparse.ArgumentParser(description="PDH/PDL Trading Bot")
        parser.add_argument('--ticker', type=str, default='AAPL', help='The stock ticker to monitor (e.g., AAPL, GOOGL, TATACAP)')
        parser.add_argument('--suffix', type=str, default='', help='The exchange suffix for the ticker (e.g., .NS for NSE)')
        args = parser.parse_args()

        asyncio.run(check_strategy(args.ticker, args.suffix))
