import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
from trading_bot import get_pdh_pdl, get_pwh_pwl, TickerState, get_vwap

class TestTradingBot(unittest.IsolatedAsyncioTestCase):

    @patch('yfinance.Ticker')
    def test_get_pdh_pdl(self, mock_ticker):
        mock_hist = pd.DataFrame({
            'High': [150.0, 155.0], 'Low': [145.0, 148.0], 'Close': [148.0, 154.0]
        }, index=pd.to_datetime(['2023-01-01', '2023-01-02']))
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_instance
        pdh, pdl = get_pdh_pdl('TEST')
        self.assertEqual(pdh, 150.0)
        self.assertEqual(pdl, 145.0)

    @patch('yfinance.Ticker')
    def test_get_pwh_pwl(self, mock_ticker):
        mock_hist = pd.DataFrame({
            'High': [160.0, 165.0, 162.0], 'Low': [155.0, 158.0, 156.0]
        })
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_instance
        pwh, pwl = get_pwh_pwl('TEST')
        self.assertEqual(pwh, 165.0)
        self.assertEqual(pwl, 155.0)

    @patch('trading_bot.get_pdh_pdl', return_value=(150.0, 145.0))
    @patch('trading_bot.get_pwh_pwl', return_value=(160.0, 140.0))
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_ticker_state_update_levels(self, mock_send_alert, mock_get_pwh_pwl, mock_get_pdh_pdl):
        state = TickerState('TEST', '.NS')
        await state.update_levels()

        self.assertEqual(state.levels['pdh'], 150.0)
        self.assertEqual(state.levels['pwh'], 160.0)
        mock_send_alert.assert_called_once()

    @patch('trading_bot.get_current_price')
    @patch('trading_bot.get_vwap')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_ticker_state_check_price_with_vwap(self, mock_send_alert, mock_get_vwap, mock_get_price):
        state = TickerState('TEST', '.NS')
        state.levels = {'pdh': 150.0, 'pdl': 145.0}
        state.alert_flags = {f"alerted_{k}": False for k in state.levels}

        # --- Test 1: Crossover with VWAP confirmation ---
        mock_get_price.return_value = 151.0
        mock_get_vwap.return_value = 150.5
        await state.check_price()
        mock_send_alert.assert_called_once()

        # --- Test 2: Crossover WITHOUT VWAP confirmation ---
        mock_send_alert.reset_mock()
        mock_get_price.return_value = 152.0
        mock_get_vwap.return_value = 152.5 # Price is below VWAP
        await state.check_price()
        mock_send_alert.assert_not_called()

if __name__ == '__main__':
    unittest.main()
