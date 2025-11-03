import yfinance as yf
import pandas as pd
import time
import telegram
import os
import argparse
import asyncio
from dotenv import load_dotenv

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

def get_current_price(ticker):
    """
    Fetches the current price of a given stock.
    """
    stock = yf.Ticker(ticker)
    # Use 'fast_info' for quicker price retrieval
    price = stock.fast_info.get('last_price')
    return price


async def check_strategy(ticker):
    """
    Checks the trading strategy for a given stock.
    """
    await send_telegram_alert(f"Trading bot started for {ticker}.")

    pdh, pdl = get_pdh_pdl(ticker)
    if not pdh or not pdl:
        message = f"Could not retrieve PDH/PDL for {ticker}"
        print(message)
        await send_telegram_alert(message)
        return

    message = f"PDH: {round(pdh, 2)}, PDL: {round(pdl, 2)} for {ticker}"
    print(message)
    await send_telegram_alert(message)

    alerted_pdh_cross = False
    alerted_pdl_cross = False

    while True:
        current_price = get_current_price(ticker)
        if current_price is None:
            print(f"Could not fetch current price for {ticker}. Skipping this iteration.")
            await asyncio.sleep(60)
            continue

        print(f"Current price for {ticker}: {round(current_price, 2)}")

        if current_price > pdh and not alerted_pdh_cross:
            message = f"Alert: {ticker} crossed above PDH! Price: {round(current_price, 2)}"
            print(message)
            await send_telegram_alert(message)
            alerted_pdh_cross = True
        elif current_price < pdh:
            # Reset the flag if the price drops back below the PDH
            alerted_pdh_cross = False

        if current_price < pdl and not alerted_pdl_cross:
            message = f"Alert: {ticker} crossed below PDL! Price: {round(current_price, 2)}"
            print(message)
            await send_telegram_alert(message)
            alerted_pdl_cross = True
        elif current_price > pdl:
            # Reset the flag if the price rises back above the PDL
            alerted_pdl_cross = False

        await asyncio.sleep(60) # Wait for 60 seconds before checking again


if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
        print("Please create a .env file and add your credentials there. See .env.example for reference.")
    else:
        parser = argparse.ArgumentParser(description="PDH/PDL Trading Bot")
        parser.add_argument('--ticker', type=str, default='AAPL', help='The stock ticker to monitor (e.g., AAPL, GOOGL, TSLA)')
        args = parser.parse_args()

        asyncio.run(check_strategy(args.ticker))
