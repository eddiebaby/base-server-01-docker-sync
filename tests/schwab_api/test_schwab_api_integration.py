"""
Test module for Schwab API Integration
:TechnologyVersion Python 3.10+
:TestingPattern UnitTesting
:AuthenticationPattern OAuth2
:SecurityPattern SecureCredentialManagement

This module contains comprehensive tests for the Schwab API integration,
including OAuth authentication flow, token refresh, and market data fetching.
"""

import os
import sys
import unittest
import pytest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
import json
import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from schwab_api.auth.oauth_integration import SchwabOAuthIntegration
from schwab_api.auth.oauth.oauth_client import OAuthClient
from schwab_api.auth.oauth.token_manager import TokenManager
from schwab_api.market_data.market_data_client import MarketDataClient
from schwab_api.config.settings import SettingsManager
from schwab_api.config.secure_storage import SecureStorage
from schwab_api.auth.exceptions import AuthenticationError, TokenError


class TestSchwabAPIIntegration(unittest.TestCase):
    """Comprehensive test cases for Schwab API integration"""
    
    def setUp(self):
        """Set up test environment"""
        # Create mock settings
        self.mock_settings = MagicMock(spec=SettingsManager)
        self.mock_settings.get_oauth_client_credentials.return_value = {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret'
        }
        self.mock_settings.get_oauth_authorize_url.return_value = 'https://api.test.com/oauth/authorize'
        self.mock_settings.get_oauth_token_url.return_value = 'https://api.test.com/oauth/token'
        self.mock_settings.get_callback_url.return_value = 'http://localhost:8000/callback'
        self.mock_settings.get.return_value = './test_storage'
        
        # Create mock secure storage
        self.mock_storage = MagicMock(spec=SecureStorage)
        self.mock_storage.retrieve.return_value = None
        
        # Mock environment variables to avoid real credentials
        self.env_patcher = patch.dict(os.environ, {
            'SCHWAB_CLIENT_ID': '',
            'SCHWAB_CLIENT_SECRET': ''
        })
        self.env_patcher.start()
        
        # Create OAuth integration with mocks
        self.oauth_integration = SchwabOAuthIntegration(
            api_type='market_data',
            settings=self.mock_settings,
            storage=self.mock_storage
        )
        
        # Mock the OAuth client
        self.mock_oauth_client = MagicMock(spec=OAuthClient)
        self.oauth_integration.oauth_client = self.mock_oauth_client
        
        # Create mock market data client
        self.mock_market_data_client = MagicMock(spec=MarketDataClient)
    
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
    
    def test_oauth_authentication_success(self):
        """Test successful OAuth authentication flow"""
        # Configure mock to simulate successful authentication
        self.mock_oauth_client.authenticate.return_value = True
        self.mock_oauth_client.is_authenticated.return_value = True
        
        # Test authentication
        result = self.oauth_integration.authenticate()
        
        # Verify results
        self.assertTrue(result)
        self.mock_oauth_client.authenticate.assert_called_once()
        
        # Verify authentication check
        self.assertTrue(self.oauth_integration.check_authentication())
        self.mock_oauth_client.is_authenticated.assert_called_once()
    
    def test_oauth_authentication_failure(self):
        """Test failed OAuth authentication flow"""
        # Configure mock to simulate failed authentication
        self.mock_oauth_client.authenticate.return_value = False
        
        # Test authentication
        result = self.oauth_integration.authenticate()
        
        # Verify results
        self.assertFalse(result)
        self.mock_oauth_client.authenticate.assert_called_once()
    
    def test_token_refresh(self):
        """Test token refresh functionality"""
        # Configure mocks for token refresh
        self.mock_oauth_client.is_authenticated.side_effect = [False, True]
        self.mock_oauth_client.authenticate.return_value = True
        
        # Mock token manager with refresh token
        mock_token_manager = MagicMock(spec=TokenManager)
        mock_token_manager.refresh_token = "test_refresh_token"
        mock_token_manager.refresh_access_token.return_value = True
        self.oauth_integration.token_manager = mock_token_manager
        
        # Test authentication (should trigger refresh)
        result = self.oauth_integration.authenticate()
        
        # Verify results
        self.assertTrue(result)
        mock_token_manager.refresh_access_token.assert_called_once()
    
    def test_token_refresh_failure(self):
        """Test token refresh failure handling"""
        # Configure mocks for token refresh failure
        self.mock_oauth_client.is_authenticated.return_value = False
        self.mock_oauth_client.authenticate.return_value = True
        
        # Mock token manager with refresh token that fails
        mock_token_manager = MagicMock(spec=TokenManager)
        mock_token_manager.refresh_token = "test_refresh_token"
        mock_token_manager.refresh_access_token.side_effect = TokenError("Refresh failed")
        self.oauth_integration.token_manager = mock_token_manager
        
        # Test authentication (should fall back to full auth)
        result = self.oauth_integration.authenticate()
        
        # Verify results
        self.assertTrue(result)
        mock_token_manager.refresh_access_token.assert_called_once()
        self.mock_oauth_client.authenticate.assert_called_once()
    
    def test_token_info(self):
        """Test token info retrieval"""
        # Configure mock for token info
        expected_info = {
            'status': 'valid',
            'api_type': 'market_data',
            'expires_in': 3600,
            'has_refresh_token': True
        }
        self.mock_oauth_client.get_token_info.return_value = expected_info
        
        # Get token info
        token_info = self.oauth_integration.get_token_info()
        
        # Verify results
        self.assertEqual(token_info, expected_info)
        self.mock_oauth_client.get_token_info.assert_called_once()
    
    @patch('schwab_api.auth.oauth_integration.SchwabOAuthIntegration.authenticate')
    def test_market_data_client_creation(self, mock_authenticate):
        """Test market data client creation with authentication"""
        # Configure mocks
        mock_authenticate.return_value = True
        
        # Create a real OAuth integration but with mocked components
        with patch('schwab_api.auth.oauth_integration.OAuthClient') as mock_oauth_client_cls:
            # Configure the mock OAuth client class
            mock_oauth_client_instance = MagicMock()
            mock_oauth_client_cls.return_value = mock_oauth_client_instance
            
            # Create the integration
            integration = SchwabOAuthIntegration(
                api_type='market_data',
                settings=self.mock_settings,
                storage=self.mock_storage
            )
            
            # Test creating a market data client
            with patch('schwab_api.market_data.market_data_client.MarketDataClient') as mock_market_data_client_cls:
                mock_market_data_client_instance = MagicMock()
                mock_market_data_client_cls.return_value = mock_market_data_client_instance
                
                # Call the function that would create a market data client
                from schwab_api_data_fetcher import authenticate_with_schwab_api
                
                # Patch the create_default_instance to return our mocked integration
                with patch('schwab_api.auth.oauth_integration.SchwabOAuthIntegration.create_default_instance', return_value=integration):
                    client = authenticate_with_schwab_api()
                    
                    # Verify results
                    self.assertIsNotNone(client)
                    mock_authenticate.assert_called_once()
                    mock_market_data_client_cls.assert_called_once_with(mock_oauth_client_instance)


class TestMarketDataFetching(unittest.TestCase):
    """Test cases for market data fetching functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create mock OAuth client
        self.mock_oauth_client = MagicMock(spec=OAuthClient)
        
        # Create market data client with mock OAuth client
        self.market_data_client = MarketDataClient(self.mock_oauth_client)
        
        # Configure mock OAuth client for API calls
        self.mock_oauth_client.get.return_value = {}
    
    def test_get_quotes(self):
        """Test fetching quotes for symbols"""
        # Configure mock response
        mock_quotes = {
            'AAPL': {
                'symbol': 'AAPL',
                'description': 'Apple Inc',
                'lastPrice': 150.25,
                'change': 2.5,
                'percentChange': 1.67,
                'volume': 45678901
            },
            'MSFT': {
                'symbol': 'MSFT',
                'description': 'Microsoft Corporation',
                'lastPrice': 280.75,
                'change': -1.25,
                'percentChange': -0.44,
                'volume': 23456789
            }
        }
        self.mock_oauth_client.get_quotes.return_value = mock_quotes
        
        # Test fetching quotes
        result = self.market_data_client.get_quotes(['AAPL', 'MSFT'])
        
        # Verify results
        self.assertEqual(result, mock_quotes)
        self.mock_oauth_client.get_quotes.assert_called_once_with(['AAPL', 'MSFT'], None)
    
    def test_get_price_history(self):
        """Test fetching price history for a symbol"""
        # Configure mock response
        mock_price_history = {
            'symbol': 'SPY',
            'candles': [
                {
                    'datetime': 1619712000000,  # 2021-04-30
                    'open': 420.25,
                    'high': 422.75,
                    'low': 419.50,
                    'close': 421.75,
                    'volume': 12345678
                },
                {
                    'datetime': 1619798400000,  # 2021-05-01
                    'open': 421.75,
                    'high': 423.50,
                    'low': 420.25,
                    'close': 422.50,
                    'volume': 9876543
                }
            ]
        }
        self.mock_oauth_client.get.return_value = mock_price_history
        
        # Test fetching price history
        result = self.market_data_client.get_price_history(
            symbol='SPY',
            period_type='day',
            period=10,
            frequency_type='daily',
            frequency=1
        )
        
        # Verify results
        self.assertEqual(result, mock_price_history)
        self.mock_oauth_client.get.assert_called_once_with('priceHistory', params={
            'symbol': 'SPY',
            'periodType': 'day',
            'period': 10,
            'frequencyType': 'day',  # Note the mapping from 'daily' to 'day'
            'frequency': 1
        })
    
    def test_get_option_chain(self):
        """Test fetching option chain for a symbol"""
        # Configure mock response
        mock_option_chain = {
            'symbol': 'AAPL',
            'status': 'SUCCESS',
            'underlying': {
                'symbol': 'AAPL',
                'description': 'Apple Inc',
                'lastPrice': 150.25
            },
            'putExpDateMap': {},
            'callExpDateMap': {}
        }
        self.mock_oauth_client.get.return_value = mock_option_chain
        
        # Test fetching option chain
        result = self.market_data_client.get_option_chain(
            symbol='AAPL',
            strike_count=10,
            include_quotes=True
        )
        
        # Verify results
        self.assertEqual(result, mock_option_chain)
        self.mock_oauth_client.get.assert_called_once_with('optionChain', params={
            'symbol': 'AAPL',
            'strikeCount': 10,
            'includeQuotes': 'true',
            'strategy': 'SINGLE'
        })
    
    def test_get_movers(self):
        """Test fetching market movers for an index"""
        # Configure mock response
        mock_movers = {
            'index': 'SPX',
            'direction': 'up',
            'change': 'percent',
            'movers': [
                {
                    'symbol': 'AAPL',
                    'description': 'Apple Inc',
                    'lastPrice': 150.25,
                    'change': 2.5,
                    'percentChange': 1.67
                },
                {
                    'symbol': 'MSFT',
                    'description': 'Microsoft Corporation',
                    'lastPrice': 280.75,
                    'change': 3.25,
                    'percentChange': 1.15
                }
            ]
        }
        self.mock_oauth_client.get.return_value = mock_movers
        
        # Test fetching movers
        result = self.market_data_client.get_movers(
            index='SPX',
            direction='up',
            change='percent'
        )
        
        # Verify results
        self.assertEqual(result, mock_movers)
        self.mock_oauth_client.get.assert_called_once_with('movers', params={
            'index': 'SPX',
            'direction': 'up',
            'change': 'percent'
        })


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling in Schwab API integration"""
    
    def setUp(self):
        """Set up test environment"""
        # Create mock OAuth client
        self.mock_oauth_client = MagicMock(spec=OAuthClient)
        
        # Create market data client with mock OAuth client
        self.market_data_client = MarketDataClient(self.mock_oauth_client)
    
    def test_authentication_error_handling(self):
        """Test handling of authentication errors"""
        # Configure mock to raise authentication error
        self.mock_oauth_client.get_quotes.side_effect = AuthenticationError("Authentication failed")
        
        # Test error handling in fetch_quotes function
        from schwab_api_data_fetcher import fetch_quotes
        
        result = fetch_quotes(self.market_data_client, ['AAPL', 'MSFT'])
        
        # Verify results
        self.assertIsNone(result)
    
    def test_network_error_handling(self):
        """Test handling of network errors"""
        # Configure mock to raise network error
        import requests
        self.mock_oauth_client.get.side_effect = requests.RequestException("Network error")
        
        # Test error handling in fetch_price_history function
        from schwab_api_data_fetcher import fetch_price_history
        
        result = fetch_price_history(self.market_data_client, 'SPY')
        
        # Verify results
        self.assertIsNone(result)
    
    def test_token_error_handling(self):
        """Test handling of token errors"""
        # Configure mock to raise token error
        self.mock_oauth_client.get_auth_headers.side_effect = TokenError("Token expired")
        self.mock_oauth_client.get.side_effect = lambda *args, **kwargs: self.mock_oauth_client.get_auth_headers()
        
        # Test error handling in fetch_option_chain function
        from schwab_api_data_fetcher import fetch_option_chain
        
        result = fetch_option_chain(self.market_data_client, 'AAPL')
        
        # Verify results
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()