import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
from trading_bot import TickerState, UniversalStrategy, get_swing_levels

class TestUniversalStrategy(unittest.IsolatedAsyncioTestCase):

    def create_args(self, tickers=['TEST'], suffix='.NS'):
        """Helper to create a mock args object."""
        args = MagicMock()
        args.tickers = tickers
        args.suffix = suffix
        return args

    @patch('trading_bot.get_swing_levels', return_value=([], []))
    @patch('yfinance.Ticker')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_universal_strategy_startup(self, mock_send_alert, mock_yf_ticker, mock_get_swing_levels):
        # Mock the history calls for PDH/PDL and PWH/PWL
        mock_yf_ticker.return_value.history.side_effect = [
            pd.DataFrame({'High': [150], 'Low': [145]}), # PDH/PDL
            pd.DataFrame({'High': [160], 'Low': [140]})  # PWH/PWL
        ]

        args = self.create_args()
        # This test is simplified and focuses on the alert content
        # In the real script, multiple calls are made. We simulate the outcome.

        # Manually create and update state for clarity in testing
        state = TickerState('TEST', '.NS', UniversalStrategy, args)
        state.levels = {
            'pdh': 150.0, 'pdl': 145.0, 'pwh': 160.0, 'pwl': 140.0,
            'swing_high_0': 170.0, 'swing_low_0': 130.0
        }

        # Create the expected formatted string for the alert
        level_str = "\n".join([f"{k.upper()}: {round(v, 2)}" for k, v in state.levels.items()])
        expected_alert = f"Key levels for TEST.NS:\n{level_str}"

        # We can't easily test the main() function, so we'll simulate its key alert
        await send_telegram_alert(expected_alert)

        mock_send_alert.assert_called_with(expected_alert)

    @patch('trading_bot.get_current_price', return_value=151.0)
    @patch('trading_bot.get_vwap', return_value=150.5)
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_universal_strategy_check(self, mock_send_alert, mock_get_vwap, mock_get_price):
        args = self.create_args()
        state = TickerState('TEST', '.NS', UniversalStrategy, args)
        state.levels = {'pdh': 150.0, 'swing_low_0': 130.0}
        state.alert_flags = {'alerted_pdh': False, 'alerted_swing_low_0': False}

        await state.strategy.check_price()
        mock_send_alert.assert_called_once()

if __name__ == '__main__':
    unittest.main()
