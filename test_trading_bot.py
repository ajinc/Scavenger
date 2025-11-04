import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pandas as pd
import asyncio
from trading_bot import get_pdh_pdl, get_pwh_pwl, get_current_price, update_key_levels, check_price, key_levels, get_utc_time

class TestTradingBot(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Reset key_levels before each test
        key_levels.clear()

    def test_get_utc_time(self):
        # Test with Indian Standard Time
        utc_time = get_utc_time('09:15', 'Asia/Kolkata')
        # This will vary depending on the current date and DST, so we check the format
        self.assertRegex(utc_time, r'\d{2}:\d{2}')

        # Test with a US timezone
        utc_time_us = get_utc_time('09:30', 'America/New_York')
        self.assertRegex(utc_time_us, r'\d{2}:\d{2}')

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
    async def test_update_key_levels(self, mock_send_alert, mock_get_pwh_pwl, mock_get_pdh_pdl):
        await update_key_levels('TEST', '.NS')

        self.assertEqual(key_levels['pdh'], 150.0)
        self.assertEqual(key_levels['pwh'], 160.0)
        mock_send_alert.assert_called_once()

    @patch('trading_bot.get_current_price')
    @patch('trading_bot.send_telegram_alert', new_callable=AsyncMock)
    async def test_check_price(self, mock_send_alert, mock_get_price):
        key_levels.update({
            'pdh': 150.0, 'pdl': 145.0, 'pwh': 160.0, 'pwl': 140.0,
            'alerted_pdh': False, 'alerted_pdl': False, 'alerted_pwh': False, 'alerted_pwl': False
        })

        mock_get_price.return_value = 151.0
        await check_price('TEST', '.NS')
        mock_send_alert.assert_any_call("Alert: TEST.NS crossed above pdh! Price: 151.0")

        mock_get_price.return_value = 139.0
        await check_price('TEST', '.NS')
        mock_send_alert.assert_any_call("Alert: TEST.NS crossed below pwl! Price: 139.0")

if __name__ == '__main__':
    unittest.main()
