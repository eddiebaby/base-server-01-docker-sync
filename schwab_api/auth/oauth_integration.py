"""
Schwab API OAuth Integration
:TechnologyVersion Python 3.10+
:AuthenticationPattern OAuth2
:SecurityPattern for credentials management
:ConfigurationAbstraction :DesignPattern

This module provides simplified integration for Schwab API OAuth authentication,
handling proper setup, storage, and token lifecycle management.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from ..config.settings import SettingsManager
from ..config.secure_storage import SecureStorage  
from .oauth.oauth_client import OAuthClient
from .oauth.token_manager import TokenManager
from .oauth.callback_server import CallbackServer
from ...config.config_manager import config_manager

# Configure logging
logger = logging.getLogger('schwab_api.auth.oauth_integration')

class SchwabOAuthIntegration:
    """
    Simplified integration for Schwab API OAuth authentication.
    
    This class provides a high-level interface for setting up and managing
    Schwab API OAuth authentication, including secure token storage and
    configuration management.
    """
    
    def __init__(
        self, 
        api_type: str = 'market_data',
        settings: Optional[SettingsManager] = None,
        storage: Optional[SecureStorage] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize the OAuth integration.
        
        Args:
            api_type: API type ('market_data' or 'accounts_trading')
            settings: Settings manager instance (created if not provided)
            storage: Secure storage instance (created if not provided)
            config_path: Path to JSON configuration file
        """
        self.api_type = api_type
        
        # Set up base paths
        self.base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.config_dir = self.base_dir / "config"
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # Set up settings manager
        self.settings = settings or SettingsManager(config_path)
        
        # Set up secure storage
        if storage:
            self.storage = storage
        else:
            storage_dir = self.settings.get('security', 'secure_storage_dir')
            # Handle relative paths
            if not os.path.isabs(storage_dir):
                storage_dir = self.base_dir / storage_dir
            self.storage = SecureStorage(str(storage_dir))
        
        # Set up token manager
        self.token_manager = TokenManager(self.storage, api_type, self.settings)
        
        # Set up callback server
        self.callback_server = CallbackServer()
        
        # Set up OAuth client
        self.oauth_client = OAuthClient(
            api_type,
            self.settings,
            self.token_manager,
            self.callback_server
        )
        
        logger.info(f"Initialized Schwab OAuth integration for {api_type} API")
    
    def get_oauth_client(self) -> OAuthClient:
        """
        Get the OAuth client.
        
        Returns:
            OAuthClient: The OAuth client instance
        """
        return self.oauth_client
    
    def check_authentication(self) -> bool:
        """
        Check if authentication is valid.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return self.oauth_client.is_authenticated()
    
    def authenticate(self) -> bool:
        """
        Authenticate with Schwab API.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        return self.oauth_client.authenticate()
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get information about the current token.
        
        Returns:
            Dict[str, Any]: Token information
        """
        return self.oauth_client.get_token_info()
    
    def revoke_tokens(self) -> bool:
        """
        Revoke current tokens.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.oauth_client.revoke_tokens()
    
    @staticmethod
    def create_default_instance(api_type: str = 'market_data') -> 'SchwabOAuthIntegration':
        """
        Create a default instance with standard configuration.
        
        Args:
            api_type: API type ('market_data' or 'accounts_trading')
            
        Returns:
            SchwabOAuthIntegration: A new instance
        """
        # Set up settings manager with ConfigManager integration
        settings = SettingsManager(config_manager_instance=config_manager)
        
        # Create and return integration instance
        return SchwabOAuthIntegration(api_type=api_type, settings=settings)
    
    @staticmethod
    def save_credentials(client_id: str, client_secret: str) -> bool:
        """
        Save credentials to .env file.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            
        Returns:
            bool: True if successful, False otherwise
        """
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        env_path = base_dir / "config" / ".env"
        
        try:
            # Read existing .env file
            env_lines = []
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add Schwab API credentials
            client_id_found = False
            client_secret_found = False
            
            for i, line in enumerate(env_lines):
                if line.startswith('SCHWAB_CLIENT_ID='):
                    env_lines[i] = f'SCHWAB_CLIENT_ID={client_id}\n'
                    client_id_found = True
                elif line.startswith('SCHWAB_CLIENT_SECRET='):
                    env_lines[i] = f'SCHWAB_CLIENT_SECRET={client_secret}\n'
                    client_secret_found = True
            
            # Add new lines if not found
            if not client_id_found:
                env_lines.append(f'SCHWAB_CLIENT_ID={client_id}\n')
            if not client_secret_found:
                env_lines.append(f'SCHWAB_CLIENT_SECRET={client_secret}\n')
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(env_lines)
                
            logger.info(f"Saved credentials to {env_path}")
            
            # Reload environment variables
            config_manager.load_env_file()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            return False