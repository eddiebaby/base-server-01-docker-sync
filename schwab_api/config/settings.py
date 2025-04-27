"""
Settings Manager for Schwab API
:TechnologyVersion Python 3.10+
:SecurityPattern for API credential management
:ConfigurationAbstraction :DesignPattern

This module provides configuration settings management for the Schwab API
by integrating with the application's ConfigManager.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Import ConfigManager from relative path
import sys
from pathlib import Path

# Add path for imports
module_path = Path(__file__).resolve().parent.parent.parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

from config.config_manager import ConfigManager, config_manager

# Configure logging
logger = logging.getLogger('schwab_api.settings')


class SettingsManager:
    """
    Manager for API configuration settings.
    :DesignPattern :ConfigurationAbstraction
    
    This class handles loading, storing, and retrieving configuration settings
    for the Schwab API client by integrating with the application's ConfigManager.
    It implements a secure configuration abstraction following security best practices.
    """
    
    # Default settings
    DEFAULT_SETTINGS = {
        'api': {
            'base_url': 'https://api.schwabapi.com/v1',
            'market_data_endpoint': '/market-data',
            'accounts_endpoint': '/accounts',
            'oauth_authorize_endpoint': '/oauth/authorize',
            'oauth_token_endpoint': '/oauth/token',
        },
        'auth': {
            'market_data_callback': 'http://127.0.0.1:8000/callback',
            'accounts_trading_callback': 'http://127.0.0.1:8000/callback',
            'token_refresh_buffer_seconds': 300,
            'auth_timeout_seconds': 300,
        },
        'security': {
            'encrypt_tokens': True,
            'secure_storage_dir': './config',
        },
        'network': {
            'request_timeout_seconds': 30,
            'max_retries': 3,
            'retry_backoff_factor': 0.5,
            'retry_status_codes': [500, 502, 503, 504],
        }
    }
    
    def __init__(self, config_path: Optional[str] = None, config_manager_instance: Optional[ConfigManager] = None):
        """
        Initialize the settings manager.
        
        Args:
            config_path (Optional[str]): Path to a JSON configuration file
            config_manager_instance (Optional[ConfigManager]): ConfigManager instance to use
        """
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.config_path = config_path
        
        # Use provided config_manager or global instance
        self.config_manager = config_manager_instance or config_manager
        
        # Load OAuth settings from ConfigManager
        self._load_oauth_settings()
        
        # Load from JSON if provided
        if config_path:
            self._load_settings(config_path)
    
    def _load_oauth_settings(self) -> None:
        """
        Load OAuth settings from ConfigManager.
        """
        try:
            oauth_config = self.config_manager.get_schwab_oauth_config()
            
            # Update settings with values from config manager
            if oauth_config.get('api_base_url'):
                self.settings['api']['base_url'] = oauth_config['api_base_url']
                
            if oauth_config.get('auth_url'):
                self.settings['api']['oauth_authorize_endpoint'] = oauth_config['auth_url'].replace(
                    self.settings['api']['base_url'], '')
                
            if oauth_config.get('token_url'):
                self.settings['api']['oauth_token_endpoint'] = oauth_config['token_url'].replace(
                    self.settings['api']['base_url'], '')
            
            if oauth_config.get('redirect_uri'):
                self.settings['auth']['market_data_callback'] = oauth_config['redirect_uri']
                self.settings['auth']['accounts_trading_callback'] = oauth_config['redirect_uri']
                
            logger.info("Loaded OAuth settings from ConfigManager")
            
        except Exception as e:
            logger.error(f"Error loading OAuth settings from ConfigManager: {str(e)}")
    
    def _load_settings(self, config_path: str) -> None:
        """
        Load settings from a JSON file.
        
        Args:
            config_path (str): Path to the JSON configuration file
        """
        if not os.path.exists(config_path):
            logger.warning(f"Config file '{config_path}' not found, using defaults")
            return
            
        try:
            with open(config_path, 'r') as f:
                user_settings = json.load(f)
                
            # Recursively update default settings with user settings
            self._update_settings(self.settings, user_settings)
            logger.info(f"Loaded settings from {config_path}")
            
        except Exception as e:
            logger.error(f"Error loading settings from {config_path}: {str(e)}")
    
    def _update_settings(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively update settings.
        
        Args:
            target (Dict[str, Any]): Target dictionary to update
            source (Dict[str, Any]): Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursive update for nested dictionaries
                self._update_settings(target[key], value)
            else:
                # Direct update for flat values
                target[key] = value
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            section (str): Settings section name
            key (str): Setting key
            default (Any, optional): Default value if not found
            
        Returns:
            Any: Setting value or default
        """
        try:
            return self.settings[section][key]
        except KeyError:
            if default is not None:
                return default
            raise KeyError(f"Setting '{section}.{key}' not found")
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            section (str): Settings section name
            key (str): Setting key
            value (Any): Setting value
        """
        if section not in self.settings:
            self.settings[section] = {}
            
        self.settings[section][key] = value
    
    def save(self, config_path: Optional[str] = None) -> bool:
        """
        Save settings to a JSON file.
        
        Args:
            config_path (Optional[str]): Path to save to, defaults to path used in constructor
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        save_path = config_path or self.config_path
        
        if not save_path:
            logger.error("No config path specified for saving settings")
            return False
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
                
            logger.info(f"Saved settings to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings to {save_path}: {str(e)}")
            return False
    
    def get_api_url(self, api_type: str) -> str:
        """
        Get the full API URL for a given API type.
        
        Args:
            api_type (str): API type ('market_data' or 'accounts_trading')
            
        Returns:
            str: Full API URL
        """
        base_url = self.get('api', 'base_url')
        
        if api_type == 'market_data':
            return base_url + self.get('api', 'market_data_endpoint')
        elif api_type == 'accounts_trading':
            return base_url + self.get('api', 'accounts_endpoint')
        else:
            raise ValueError(f"Unknown API type: {api_type}")
    
    def get_oauth_authorize_url(self) -> str:
        """
        Get the OAuth authorization URL.
        
        Returns:
            str: OAuth authorization URL
        """
        # First check direct environment variable
        auth_url = os.environ.get('SCHWAB_AUTH_URL')
        if auth_url:
            return auth_url
            
        # Then try to get from config manager
        oauth_config = self.config_manager.get_schwab_oauth_config()
        if 'auth_url' in oauth_config and oauth_config['auth_url']:
            return oauth_config['auth_url']
        
        # Fall back to settings
        base_url = self.get('api', 'base_url')
        endpoint = self.get('api', 'oauth_authorize_endpoint')
        return base_url + endpoint
    
    def get_oauth_token_url(self) -> str:
        """
        Get the OAuth token URL.
        
        Returns:
            str: OAuth token URL
        """
        # First check direct environment variable
        token_url = os.environ.get('SCHWAB_TOKEN_URL')
        if token_url:
            return token_url
            
        # Then try to get from config manager
        oauth_config = self.config_manager.get_schwab_oauth_config()
        if 'token_url' in oauth_config and oauth_config['token_url']:
            return oauth_config['token_url']
        
        # Fall back to settings
        base_url = self.get('api', 'base_url')
        endpoint = self.get('api', 'oauth_token_endpoint')
        return base_url + endpoint
    
    def get_callback_url(self, api_type: str) -> str:
        """
        Get the OAuth callback URL for the specified API type.
        
        Args:
            api_type (str): API type ('market_data' or 'accounts_trading')
            
        Returns:
            str: Callback URL
        """
        # First check direct environment variable
        redirect_uri = os.environ.get('SCHWAB_REDIRECT_URI')
        if redirect_uri:
            return redirect_uri
            
        # Then try to get from config manager
        oauth_config = self.config_manager.get_schwab_oauth_config()
        if 'redirect_uri' in oauth_config and oauth_config['redirect_uri']:
            return oauth_config['redirect_uri']
        
        # Fall back to settings
        if api_type == 'market_data':
            return self.get('auth', 'market_data_callback')
        elif api_type == 'accounts_trading':
            return self.get('auth', 'accounts_trading_callback')
        else:
            raise ValueError(f"Unknown API type: {api_type}")
    
    def get_oauth_client_credentials(self) -> Dict[str, str]:
        """
        Get the OAuth client credentials.
        
        Returns:
            Dict[str, str]: Client ID and client secret
        """
        # First check direct environment variables
        client_id = os.environ.get('SCHWAB_CLIENT_ID', '')
        client_secret = os.environ.get('SCHWAB_CLIENT_SECRET', '')
        
        # If both are set in environment, use them
        if client_id and client_secret:
            return {
                'client_id': client_id,
                'client_secret': client_secret
            }
        
        # Otherwise, get from config manager
        oauth_config = self.config_manager.get_schwab_oauth_config()
        
        # Prioritize environment variables if set
        return {
            'client_id': client_id or oauth_config.get('client_id', ''),
            'client_secret': client_secret or oauth_config.get('client_secret', '')
        }