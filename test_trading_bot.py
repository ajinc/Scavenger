import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
import asyncio
from trading_bot import get_pdh_pdl, get_pwh_pwl, get_current_price, check_strategy, update_key_levels, key_levels

class TestTradingBot(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Reset key_levels before each test
        key_levels.clear()

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

    @patch('yfinance.Ticker')
    def test_get_current_price_fast_info(self, mock_ticker):
        mock_instance = MagicMock()
        mock_instance.fast_info.get.return_value = 160.0
        mock_ticker.return_value = mock_instance
        price = get_current_price('TEST')
        self.assertEqual(price, 160.0)

    @patch('trading_bot.get_pdh_pdl', return_value=(150.0, 145.0))
    @patch('trading_bot.get_pwh_pwl', return_value=(160.0, 140.0))
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_update_key_levels(self, mock_send_alert, mock_get_pwh_pwl, mock_get_pdh_pdl):
        await update_key_levels('TEST', '.NS')

        self.assertEqual(key_levels['pdh'], 150.0)
        self.assertEqual(key_levels['pwh'], 160.0)
        mock_send_alert.assert_called_once()

    @patch('trading_bot.get_current_price')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    @patch('asyncio.sleep', return_value=None)
    @patch('schedule.run_pending', return_value=None)
    async def test_check_strategy(self, mock_run_pending, mock_sleep, mock_send_alert, mock_get_price):
        # Pre-populate key_levels for the test
        key_levels.update({
            'pdh': 150.0, 'pdl': 145.0, 'pwh': 160.0, 'pwl': 140.0,
            'alerted_pdh': False, 'alerted_pdl': False, 'alerted_pwh': False, 'alerted_pwl': False
        })

        mock_get_price.side_effect = [151.0, 161.0, 144.0, 139.0, ValueError("Stop test")]

        with self.assertRaises(ValueError, msg="Stop test"):
            await check_strategy('TEST', '.NS')

        self.assertEqual(mock_send_alert.call_count, 4)
        mock_send_alert.assert_any_call("Alert: TEST.NS crossed above pdh! Price: 151.0")
        mock_send_alert.assert_any_call("Alert: TEST.NS crossed above pwh! Price: 161.0")
        mock_send_alert.assert_any_call("Alert: TEST.NS crossed below pdl! Price: 144.0")
        mock_send_alert.assert_any_call("Alert: TEST.NS crossed below pwl! Price: 139.0")

if __name__ == '__main__':
    unittest.main()
