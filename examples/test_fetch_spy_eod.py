import unittest
from unittest.mock import Mock, patch
import datetime
import sys
from io import StringIO

# Setup mocks BEFORE importing the module to test
# Mock Path and sys.path.insert to prevent the actual path manipulation
path_mock = Mock()
path_mock.resolve.return_value.parent.parent = "mocked_parent_path"
sys.path_insert_original = sys.path.insert
sys.path.insert = Mock()

# Mock the critical imports completely
sys.modules['schwab_api'] = Mock()
sys.modules['schwab_api.auth'] = Mock()
sys.modules['schwab_api.auth.oauth_integration'] = Mock()
sys.modules['schwab_api.auth.oauth_integration.SchwabOAuthIntegration'] = Mock()
sys.modules['schwab_api.market_data'] = Mock()
sys.modules['schwab_api.market_data.market_data_client'] = Mock()
sys.modules['schwab_api.market_data.market_data_client.MarketDataClient'] = Mock()

# Now patch Path before importing
with patch('pathlib.Path', return_value=path_mock):
    # Import after mocking
    from fetch_spy_eod import get_previous_friday, fetch_spy_eod_data, display_price_data

# Restore sys.path.insert for cleanup
sys.path.insert = sys.path_insert_original

class TestFetchSpyEOD(unittest.TestCase):
    """Test suite for fetch_spy_eod.py"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.sample_price_data = {
            'candles': [{
                'datetime': 1682640000000,  # 2023-04-28
                'open': 412.50,
                'high': 415.75,
                'low': 411.25,
                'close': 415.00,
                'volume': 75000000
            }]
        }

    def test_get_previous_friday_basic(self):
        """Test basic previous Friday calculation"""
        # Mock today as Wednesday 2025-04-23
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value = datetime.date(2025, 4, 23)
            self.assertEqual(get_previous_friday(), '2025-04-18')

    def test_get_previous_friday_when_friday(self):
        """Test when current day is Friday"""
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value = datetime.date(2025, 4, 25)
            self.assertEqual(get_previous_friday(), '2025-04-18')

    def test_get_previous_friday_month_boundary(self):
        """Test calculation across month boundary"""
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value = datetime.date(2025, 5, 1)
            self.assertEqual(get_previous_friday(), '2025-04-25')

    def test_get_previous_friday_year_boundary(self):
        """Test calculation across year boundary"""
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value = datetime.date(2025, 1, 2)
            self.assertEqual(get_previous_friday(), '2024-12-27')

    def test_fetch_spy_eod_data_success(self):
        """Test successful data fetch"""
        self.mock_client.get_price_history.return_value = self.sample_price_data
        result = fetch_spy_eod_data(self.mock_client, '2025-04-25')
        
        self.mock_client.get_price_history.assert_called_once_with(
            symbol="SPY",
            start_date='2025-04-25',
            end_date='2025-04-25',
            frequency="daily"
        )
        self.assertEqual(result, self.sample_price_data)

    def test_fetch_spy_eod_data_failure(self):
        """Test data fetch failure"""
        self.mock_client.get_price_history.side_effect = Exception("API Error")
        result = fetch_spy_eod_data(self.mock_client, '2025-04-25')
        self.assertIsNone(result)

    def test_display_price_data_success(self):
        """Test successful price data display"""
        captured_output = StringIO()
        sys.stdout = captured_output
        
        display_price_data(self.sample_price_data)
        output = captured_output.getvalue()
        
        sys.stdout = sys.__stdout__
        
        self.assertIn("Date: 2023-04-28", output)
        self.assertIn("Open: $412.50", output)
        self.assertIn("High: $415.75", output)
        self.assertIn("Low: $411.25", output)
        self.assertIn("Close: $415.00", output)
        self.assertIn("Volume: 75,000,000", output)
        self.assertIn("Day's Change: +$2.50 (+0.61%)", output)

    def test_display_price_data_no_data(self):
        """Test display with no price data"""
        captured_output = StringIO()
        sys.stdout = captured_output
        
        display_price_data({})
        output = captured_output.getvalue()
        
        sys.stdout = sys.__stdout__
        
        self.assertIn("No price data available", output)

    def test_display_price_data_empty_candles(self):
        """Test display with empty candles list"""
        captured_output = StringIO()
        sys.stdout = captured_output
        
        display_price_data({'candles': []})
        output = captured_output.getvalue()
        
        sys.stdout = sys.__stdout__
        
        self.assertIn("No price data available", output)

if __name__ == '__main__':
    unittest.main()