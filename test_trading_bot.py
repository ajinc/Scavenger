import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
from trading_bot import TickerState, LevelsStrategy, OrbStrategy

class TestStrategies(unittest.IsolatedAsyncioTestCase):

    def create_args(self, strategy='levels', tickers=['TEST'], suffix='.NS', market_open='09:15', timezone='Asia/Kolkata', orb_minutes=15):
        """Helper to create a mock args object."""
        args = MagicMock()
        args.strategy = strategy
        args.tickers = tickers
        args.suffix = suffix
        args.market_open = market_open
        args.timezone = timezone
        args.orb_minutes = orb_minutes
        return args

    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    @patch('trading_bot.LevelsStrategy._get_pdh_pdl', return_value=(150.0, 145.0))
    @patch('trading_bot.LevelsStrategy._get_pwh_pwl', return_value=(160.0, 140.0))
    async def test_levels_strategy_update(self, mock_get_pwh_pwl, mock_get_pdh_pdl, mock_send_alert):
        args = self.create_args()
        state = TickerState('TEST', '.NS', LevelsStrategy, args)
        await state.strategy.update_levels()

        self.assertEqual(state.levels['pdh'], 150.0)
        self.assertEqual(state.levels['pwh'], 160.0)
        mock_send_alert.assert_called_once()

    @patch('trading_bot.get_current_price', return_value=151.0)
    @patch('trading_bot.get_vwap', return_value=150.5)
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_levels_strategy_check(self, mock_send_alert, mock_get_vwap, mock_get_price):
        args = self.create_args()
        state = TickerState('TEST', '.NS', LevelsStrategy, args)
        state.levels = {'pdh': 150.0}
        state.alert_flags = {'alerted_pdh': False}

        await state.strategy.check_price()
        mock_send_alert.assert_called_once()

    @patch('yfinance.Ticker')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_orb_strategy_update(self, mock_send_alert, mock_yf_ticker):
        # Mock intraday data for the opening range
        mock_df = pd.DataFrame({
            'High': [102.0, 103.0, 101.5],
            'Low': [99.0, 100.5, 99.5]
        }, index=pd.to_datetime(['09:15', '09:20', '09:25']))

        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_df
        mock_yf_ticker.return_value = mock_instance

        args = self.create_args(strategy='orb')
        state = TickerState('TEST', '.NS', OrbStrategy, args)

        # To prevent waiting in test, we'll patch sleep
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await state.strategy.update_levels()

        self.assertEqual(state.levels['orb_high'], 103.0)
        self.assertEqual(state.levels['orb_low'], 99.0)
        mock_send_alert.assert_called_once()

if __name__ == '__main__':
    unittest.main()
