import pandas as pd
import asyncio
import telegram
import os
import argparse
import pytz
from scipy.signal import find_peaks
from dotenv import load_dotenv
from datetime import date, timedelta, datetime
from dhan_client import DhanClient

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# --- Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
dhan = DhanClient()

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
def get_intraday_dataframe(ticker):
    try:
        data = dhan.get_intraday_data(ticker)
        if not data or 'open' not in data or not data['open']:
            return pd.DataFrame()

        df = pd.DataFrame({
            'Open': data['open'],
            'High': data['high'],
            'Low': data['low'],
            'Close': data['close'],
            'Volume': data['volume'],
            'Timestamp': pd.to_datetime(data['start_Time'], unit='s')
        })
        df.set_index('Timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching intraday data for {ticker}: {e}")
        return pd.DataFrame()

def get_current_price(df):
    return df.iloc[-1]['Close'] if not df.empty else None

def get_vwap(df):
    if df.empty or 'Volume' not in df.columns or df['Volume'].sum() == 0:
        return None
    df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    return df.iloc[-1]['VWAP']

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
        today = date.today()
        hist_5d_data = dhan.get_historical_data(self.ts.full_ticker, today - timedelta(days=7), today)
        hist_5d = self._create_dataframe_from_historical(hist_5d_data)

        if len(hist_5d) > 1:
            levels['pdh'] = hist_5d.iloc[-2]['High']
            levels['pdl'] = hist_5d.iloc[-2]['Low']

        if not hist_5d.empty:
            levels['pwh'] = hist_5d['High'].max()
            levels['pwl'] = hist_5d['Low'].min()

        swing_highs, swing_lows = await self._get_swing_levels()
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
        intraday_df = get_intraday_dataframe(self.ts.full_ticker)
        if intraday_df.empty:
            return

        price = get_current_price(intraday_df)
        vwap = get_vwap(intraday_df)

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

    def _create_dataframe_from_historical(self, data):
        if not data or 'open' not in data or not data['open']:
            return pd.DataFrame()
        df = pd.DataFrame({
            'Open': data['open'],
            'High': data['high'],
            'Low': data['low'],
            'Close': data['close'],
            'Volume': data['volume'],
            'Timestamp': pd.to_datetime(data['start_Time'], unit='s')
        })
        df.set_index('Timestamp', inplace=True)
        return df

    async def _get_swing_levels(self, months=6, prominence=0.1):
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        hist_data = dhan.get_historical_data(self.ts.full_ticker, start_date, end_date)
        hist = self._create_dataframe_from_historical(hist_data)

        if hist.empty: return [], []

        price_range = hist['High'].max() - hist['Low'].min()
        required_prominence = price_range * prominence
        high_peaks, _ = find_peaks(hist['High'], prominence=required_prominence)
        low_peaks, _ = find_peaks(-hist['Low'], prominence=required_prominence)

        return hist.iloc[high_peaks]['High'].nlargest(3).tolist(), hist.iloc[low_peaks]['Low'].nsmallest(3).tolist()

class ORBStrategy(Strategy):
    async def update_levels(self):
        # ORB levels are calculated intraday, so this is a placeholder
        self.ts.levels = {}
        self.ts.alert_flags = {}
        return True

    async def check_price(self):
        # This is a simplified ORB logic. A real implementation would be more complex.
        now = datetime.now(pytz.timezone(self.args.timezone))
        market_open_time = now.replace(hour=self.args.market_open.hour, minute=self.args.market_open.minute, second=0, microsecond=0)
        orb_end_time = market_open_time + timedelta(minutes=self.args.orb_minutes)

        if 'orb_high' not in self.ts.levels and now > orb_end_time:
            # Calculate ORB
            hist_data = dhan.get_historical_data(self.ts.full_ticker, market_open_time.date(), now.date())
            df = self._create_dataframe_from_historical(hist_data)
            orb_df = df.between_time(market_open_time.time(), orb_end_time.time())
            if not orb_df.empty:
                self.ts.levels['orb_high'] = orb_df['High'].max()
                self.ts.levels['orb_low'] = orb_df['Low'].min()
                self.ts.alert_flags = {'alerted_orb_high': False, 'alerted_orb_low': False}
                await send_telegram_alert(f"ORB levels for {self.ts.full_ticker}: High={self.ts.levels['orb_high']}, Low={self.ts.levels['orb_low']}")

        if 'orb_high' in self.ts.levels:
            # Check for breakout
            price = get_current_price(get_intraday_dataframe(self.ts.full_ticker))
            if price:
                if price > self.ts.levels['orb_high'] and not self.ts.alert_flags['alerted_orb_high']:
                    await send_telegram_alert(f"ORB High Breakout for {self.ts.full_ticker} at {price}")
                    self.ts.alert_flags['alerted_orb_high'] = True
                elif price < self.ts.levels['orb_low'] and not self.ts.alert_flags['alerted_orb_low']:
                    await send_telegram_alert(f"ORB Low Breakout for {self.ts.full_ticker} at {price}")
                    self.ts.alert_flags['alerted_orb_low'] = True

    def _create_dataframe_from_historical(self, data):
        if not data or 'open' not in data or not data['open']:
            return pd.DataFrame()
        df = pd.DataFrame({
            'Open': data['open'],
            'High': data['high'],
            'Low': data['low'],
            'Close': data['close'],
            'Volume': data['volume'],
            'Timestamp': pd.to_datetime(data['start_Time'], unit='s')
        })
        df.set_index('Timestamp', inplace=True)
        return df

# --- Ticker State ---
class TickerState:
    def __init__(self, ticker, suffix, strategy_class, args):
        self.full_ticker = f"{ticker}{suffix}"
        self.levels = {}
        self.alert_flags = {}
        self.strategy = strategy_class(self, args)

# --- Main Execution ---
async def daily_level_update_task(states):
    while True:
        # Schedule the next update for a specific time, e.g., 8:00 AM UTC
        now = datetime.utcnow()
        next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)

        sleep_seconds = (next_run - now).total_seconds()
        await asyncio.sleep(sleep_seconds)

        print("Running daily level update...")
        await asyncio.gather(*(s.strategy.update_levels() for s in states))

async def price_checker_task(states):
    while True:
        await asyncio.gather(*(s.strategy.check_price() for s in states))
        await asyncio.sleep(60)

async def main(args):
    strategy_map = {"universal": UniversalStrategy, "orb": ORBStrategy}
    strategy_class = strategy_map.get(args.strategy)
    if not strategy_class:
        print(f"Unknown strategy: {args.strategy}")
        return

    await send_telegram_alert(f"Bot starting with '{args.strategy}' strategy for: {', '.join(args.tickers)}.")

    states = [TickerState(t, args.suffix, strategy_class, args) for t in args.tickers]
    await asyncio.gather(*(s.strategy.update_levels() for s in states))

    # Start the background tasks
    asyncio.create_task(price_checker_task(states))
    asyncio.create_task(daily_level_update_task(states))

    # Keep the main function alive
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Missing Telegram credentials in .env file.")
    else:
        parser = argparse.ArgumentParser(description="A multi-strategy, multi-stock trading bot.")
        parser.add_argument('--strategy', default='universal', choices=['universal', 'orb'], help='The trading strategy to use.')
        parser.add_argument('--tickers', nargs='+', default=['RELIANCE-EQ'], help='List of stock tickers.')
        parser.add_argument('--suffix', default='', help='Exchange suffix for tickers.')
        parser.add_argument('--orb-minutes', type=int, default=15, help='Opening range breakout in minutes.')
        parser.add_argument('--market-open', type=lambda s: datetime.strptime(s, '%H:%M').time(), default='09:15', help='Market open time (HH:MM).')
        parser.add_argument('--timezone', default='Asia/Kolkata', help='The timezone for the market.')
        args = parser.parse_args()

        try:
            asyncio.run(main(args))
        except KeyboardInterrupt:
            print("Bot stopped by user.")
