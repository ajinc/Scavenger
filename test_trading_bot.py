import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from trading_bot import get_pdh_pdl, get_current_price, check_strategy

class TestTradingBot(unittest.TestCase):

    @patch('yfinance.Ticker')
    def test_get_pdh_pdl(self, mock_ticker):
        # Mock the yfinance Ticker object and its history method
        mock_hist = pd.DataFrame({
            'High': [150.0, 155.0],
            'Low': [145.0, 148.0],
            'Close': [148.0, 154.0]
        }, index=pd.to_datetime(['2023-01-01', '2023-01-02']))
        mock_instance = MagicMock()
        mock_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_instance

        pdh, pdl = get_pdh_pdl('TEST')
        self.assertEqual(pdh, 150.0)
        self.assertEqual(pdl, 145.0)

    @patch('yfinance.Ticker')
    def test_get_current_price(self, mock_ticker):
        # Mock the yfinance Ticker object and its fast_info attribute
        mock_instance = MagicMock()
        mock_instance.fast_info.get.return_value = 160.0
        mock_ticker.return_value = mock_instance

        price = get_current_price('TEST')
        self.assertEqual(price, 160.0)

    @patch('trading_bot.get_pdh_pdl')
    @patch('trading_bot.get_current_price')
    @patch('trading_bot.send_telegram_alert')
    @patch('time.sleep', return_value=None)
    def test_check_strategy(self, mock_sleep, mock_send_telegram_alert, mock_get_current_price, mock_get_pdh_pdl):
        mock_get_pdh_pdl.return_value = (150.0, 145.0)

        # Simulate a sequence of prices, then raise an exception to stop the loop.
        mock_get_current_price.side_effect = [151.0, 152.0, 149.0, 144.0, 146.0, ValueError("Stop test")]

        with self.assertRaises(ValueError, msg="Stop test"):
            check_strategy('TEST')

        # Initial calls: bot started, and PDH/PDL info
        mock_send_telegram_alert.assert_any_call('Trading bot started for TEST.')
        mock_send_telegram_alert.assert_any_call('PDH: 150.0, PDL: 145.0 for TEST')

        # Price crosses PDH at 151.0
        mock_send_telegram_alert.assert_any_call('Alert: TEST crossed above PDH! Price: 151.0')

        # Price crosses PDL at 144.0
        mock_send_telegram_alert.assert_any_call('Alert: TEST crossed below PDL! Price: 144.0')

        # Total alerts: startup, pdh/pdl, pdh cross, pdl cross = 4
        self.assertEqual(mock_send_telegram_alert.call_count, 4)


if __name__ == '__main__':
    unittest.main()
