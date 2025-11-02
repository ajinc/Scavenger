import yfinance as yf
import pandas as pd
import time
import telegram
import os

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize the bot
if TELEGRAM_BOT_TOKEN:
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
else:
    bot = None

def send_telegram_alert(message):
    """
    Sends a message to the specified Telegram chat.
    """
    if not bot or not TELEGRAM_CHAT_ID:
        print("Telegram bot not configured. Skipping alert.")
        return
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
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
    return stock.info.get('regularMarketPrice')


def check_strategy(ticker):
    """
    Checks the trading strategy for a given stock.
    """
    send_telegram_alert(f"Trading bot started for {ticker}.")

    pdh, pdl = get_pdh_pdl(ticker)
    if not pdh or not pdl:
        message = f"Could not retrieve PDH/PDL for {ticker}"
        print(message)
        send_telegram_alert(message)
        return

    message = f"PDH: {pdh}, PDL: {pdl} for {ticker}"
    print(message)
    send_telegram_alert(message)

    alerted_pdh_cross = False
    alerted_pdl_cross = False

    while True:
        current_price = get_current_price(ticker)
        if current_price is None:
            print(f"Could not fetch current price for {ticker}. Skipping this iteration.")
            time.sleep(60)
            continue

        print(f"Current price for {ticker}: {current_price}")

        if current_price > pdh and not alerted_pdh_cross:
            message = f"Alert: {ticker} crossed above PDH at {current_price}!"
            print(message)
            send_telegram_alert(message)
            alerted_pdh_cross = True
        elif current_price < pdh:
            alerted_pdh_cross = False

        if current_price < pdl and not alerted_pdl_cross:
            message = f"Alert: {ticker} crossed below PDL at {current_price}!"
            print(message)
            send_telegram_alert(message)
            alerted_pdl_cross = True
        elif current_price > pdl:
            alerted_pdl_cross = False

        time.sleep(60) # Wait for 60 seconds before checking again


if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Please set the TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
    else:
        ticker = "AAPL"  # Example ticker
        check_strategy(ticker)
