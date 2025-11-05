import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
from trading_bot import TickerState, UniversalStrategy

class TestUniversalStrategy(unittest.IsolatedAsyncioTestCase):

    def create_args(self, tickers=['TEST'], suffix='.NS'):
        """Helper to create a mock args object."""
        args = MagicMock()
        args.tickers = tickers
        args.suffix = suffix
        return args

    @patch('trading_bot.UniversalStrategy._get_swing_levels', return_value=([], []))
    @patch('yfinance.Ticker')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_update_levels_robustness(self, mock_send_alert, mock_yf_ticker, mock_get_swing_levels):
        # Simulate yfinance returning incomplete data (e.g., during a holiday)
        mock_yf_ticker.return_value.history.side_effect = [
            pd.DataFrame({'High': [150], 'Low': [145]}), # Not enough data for PDH/PDL
            pd.DataFrame({'High': [160], 'Low': [140]})
        ]

        args = self.create_args()
        state = TickerState('TEST', '.NS', UniversalStrategy, args)

        await state.strategy.update_levels()

        # Check that the bot correctly identifies the missing levels
        # but still includes the ones it could find.
        self.assertNotIn('pdh', state.levels)
        self.assertIn('pwh', state.levels)
        mock_send_alert.assert_called_once()

    @patch('trading_bot.get_current_price', return_value=151.0)
    @patch('trading_bot.get_vwap', return_value=150.5)
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_check_price_logic(self, mock_send_alert, mock_get_vwap, mock_get_price):
        args = self.create_args()
        state = TickerState('TEST', '.NS', UniversalStrategy, args)
        state.levels = {'pdh': 150.0}
        state.alert_flags = {'alerted_pdh': False}

        await state.strategy.check_price()
        mock_send_alert.assert_called_once()

if __name__ == '__main__':
    unittest.main()
