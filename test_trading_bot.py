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
        # Simulate yfinance returning incomplete data
        mock_yf_ticker.return_value.history.side_effect = [
            pd.DataFrame({'High': [150], 'Low': [145]}),
            pd.DataFrame({'High': [160], 'Low': [140]})
        ]

        args = self.create_args()
        state = TickerState('TEST', '.NS', UniversalStrategy, args)

        await state.strategy.update_levels()

        self.assertNotIn('pdh', state.levels)
        self.assertIn('pwh', state.levels)
        mock_send_alert.assert_called_once()

    @patch('trading_bot.get_current_price')
    @patch('trading_bot.get_vwap')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_breakout_alert_logic(self, mock_send_alert, mock_get_vwap, mock_get_price):
        """A comprehensive test to ensure breakout alerts are sent correctly."""
        args = self.create_args()
        state = TickerState('TEST', '.NS', UniversalStrategy, args)

        # Setup the initial state
        state.levels = {'pdh': 150.0, 'pdl': 145.0}
        state.alert_flags = {'alerted_pdh': False, 'alerted_pdl': False}

        # --- Test 1: Price breaks above PDH with VWAP confirmation ---
        mock_get_price.return_value = 151.0
        mock_get_vwap.return_value = 150.5

        await state.strategy.check_price()

        # Verify that an alert was sent
        mock_send_alert.assert_called_once()
        self.assertTrue(state.alert_flags['alerted_pdh'])

        # --- Test 2: Price is still above, ensure no duplicate alert ---
        mock_send_alert.reset_mock()
        await state.strategy.check_price()
        mock_send_alert.assert_not_called()

        # --- Test 3: Price drops below PDH, resetting the flag ---
        mock_get_price.return_value = 149.0
        await state.strategy.check_price()
        self.assertFalse(state.alert_flags['alerted_pdh'])

    @patch('trading_bot.get_current_price')
    @patch('trading_bot.get_vwap')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_breakout_alert_for_index_ticker(self, mock_send_alert, mock_get_vwap, mock_get_price):
        """Test that alerts are sent for index tickers where VWAP is unavailable."""
        args = self.create_args(tickers=['^NSEI'], suffix='')
        state = TickerState('^NSEI', '', UniversalStrategy, args)

        state.levels = {'pdh': 25000.0}
        state.alert_flags = {'alerted_pdh': False}

        # Simulate VWAP being unavailable, which is typical for an index
        mock_get_vwap.return_value = None
        mock_get_price.return_value = 25001.0

        await state.strategy.check_price()

        mock_send_alert.assert_called_once()
        self.assertTrue(state.alert_flags['alerted_pdh'])

if __name__ == '__main__':
    unittest.main()
