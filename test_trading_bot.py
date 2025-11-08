import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
from trading_bot import TickerState, UniversalStrategy

class TestUniversalStrategy(unittest.IsolatedAsyncioTestCase):

    def create_args(self, tickers=['RELIANCE.NS'], suffix=''):
        """Helper to create a mock args object."""
        args = MagicMock()
        args.tickers = tickers
        args.suffix = suffix
        return args

    def mock_intraday_data(self, price, volume):
        """Creates a mock intraday DataFrame."""
        return pd.DataFrame({
            'Close': [price -1, price],
            'Volume': [1000, volume],
        })

    @patch('trading_bot.dhan.get_historical_data')
    @patch('trading_bot.get_intraday_dataframe')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_breakout_alert_logic_with_vwap(self, mock_send_alert, mock_get_intraday_df, mock_get_historical):
        """Test breakout alert with VWAP confirmation."""
        args = self.create_args()
        state = TickerState('RELIANCE.NS', '', UniversalStrategy, args)

        state.levels = {'pdh': 150.0}
        state.alert_flags = {'alerted_pdh': False}

        # Simulate price breaking out with VWAP confirmation
        mock_get_intraday_df.return_value = self.mock_intraday_data(151.0, 1000)

        await state.strategy.check_price()

        mock_send_alert.assert_called_once()
        self.assertTrue(state.alert_flags['alerted_pdh'])

        # --- Test no duplicate alert ---
        mock_send_alert.reset_mock()
        await state.strategy.check_price()
        mock_send_alert.assert_not_called()

    @patch('trading_bot.dhan.get_historical_data')
    @patch('trading_bot.get_intraday_dataframe')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_breakout_alert_for_index_without_vwap(self, mock_send_alert, mock_get_intraday_df, mock_get_historical):
        """Test breakout alert for an index ticker where VWAP is unavailable."""
        args = self.create_args(tickers=['^NSEI'])
        state = TickerState('^NSEI', '', UniversalStrategy, args)

        state.levels = {'pdh': 25000.0}
        state.alert_flags = {'alerted_pdh': False}

        # Simulate VWAP being unavailable (Volume is 0)
        mock_get_intraday_df.return_value = pd.DataFrame({'Close': [25001.0], 'Volume': [0]})

        await state.strategy.check_price()

        mock_send_alert.assert_called_once()
        self.assertTrue(state.alert_flags['alerted_pdh'])

if __name__ == '__main__':
    unittest.main()
