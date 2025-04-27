"""
Test module for Schwab API OAuth Integration
:TechnologyVersion Python 3.10+
:TestingPattern UnitTesting
:SecurityPattern for credentials management

This module contains tests for the Schwab API OAuth integration components.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from schwab_api.auth.oauth_integration import SchwabOAuthIntegration
from schwab_api.config.settings import SettingsManager
from schwab_api.config.secure_storage import SecureStorage
from schwab_api.auth.oauth.token_manager import TokenManager
from schwab_api.auth.oauth.oauth_client import OAuthClient


class TestOAuthIntegration(unittest.TestCase):
    """Test cases for the OAuth integration module"""
    
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
    
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
    
    def test_initialization(self):
        """Test proper initialization of OAuth integration"""
        # Create integration instance with mocks
        integration = SchwabOAuthIntegration(
            api_type='market_data',
            settings=self.mock_settings,
            storage=self.mock_storage
        )
        
        # Verify initialization
        self.assertEqual(integration.api_type, 'market_data')
        self.assertIsInstance(integration.oauth_client, OAuthClient)
        self.assertIsInstance(integration.token_manager, TokenManager)
    
    @patch('schwab_api.auth.oauth.oauth_client.OAuthClient.is_authenticated')
    def test_check_authentication(self, mock_is_authenticated):
        """Test authentication check"""
        mock_is_authenticated.return_value = True
        
        integration = SchwabOAuthIntegration(
            api_type='market_data',
            settings=self.mock_settings,
            storage=self.mock_storage
        )
        
        # Verify authentication check
        self.assertTrue(integration.check_authentication())
        mock_is_authenticated.assert_called_once()
    
    @patch('schwab_api.auth.oauth.oauth_client.OAuthClient.authenticate')
    def test_authenticate(self, mock_authenticate):
        """Test authentication"""
        mock_authenticate.return_value = True
        
        integration = SchwabOAuthIntegration(
            api_type='market_data',
            settings=self.mock_settings,
            storage=self.mock_storage
        )
        
        # Verify authentication
        self.assertTrue(integration.authenticate())
        mock_authenticate.assert_called_once()
    
    @patch('schwab_api.auth.oauth.oauth_client.OAuthClient.get_token_info')
    def test_get_token_info(self, mock_get_token_info):
        """Test token info retrieval"""
        mock_get_token_info.return_value = {
            'status': 'valid',
            'expires_in': 3600
        }
        
        integration = SchwabOAuthIntegration(
            api_type='market_data',
            settings=self.mock_settings,
            storage=self.mock_storage
        )
        
        # Verify token info
        token_info = integration.get_token_info()
        self.assertEqual(token_info['status'], 'valid')
        self.assertEqual(token_info['expires_in'], 3600)
        mock_get_token_info.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', create=True)
    @patch('config.config_manager.config_manager.load_env_file')
    def test_save_credentials(self, mock_load_env, mock_open, mock_exists):
        """Test saving credentials"""
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.readlines.return_value = [
            'PGDB_HOST=localhost\n',
            'PGDB_PORT=5432\n'
        ]
        
        # Test save_credentials static method
        result = SchwabOAuthIntegration.save_credentials('test_id', 'test_secret')
        
        # Verify file operations
        self.assertTrue(result)
        mock_file.writelines.assert_called_once()
        mock_load_env.assert_called_once()
    
    @patch('schwab_api.config.settings.SettingsManager')
    @patch('schwab_api.auth.oauth_integration.SchwabOAuthIntegration.__init__')
    def test_create_default_instance(self, mock_init, mock_settings_cls):
        """Test creating default instance"""
        mock_init.return_value = None
        mock_settings_instance = MagicMock()
        mock_settings_cls.return_value = mock_settings_instance
        
        # Create default instance
        result = SchwabOAuthIntegration.create_default_instance('market_data')
        
        # Verify instance creation
        self.assertIsInstance(result, SchwabOAuthIntegration)
        mock_init.assert_called_once()


if __name__ == '__main__':
    unittest.main()