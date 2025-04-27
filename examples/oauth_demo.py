#!/usr/bin/env python
"""
Schwab API OAuth Authentication Demo
:TechnologyVersion Python 3.10+
:AuthenticationPattern OAuth2
:SecurityPattern for credentials management

This script demonstrates how to use the Schwab API OAuth client to authenticate
and retrieve market data, following the official Schwab API protocol.
It securely manages credentials using environment variables or .env file.
"""

import os
import sys
import json
import logging
import argparse
import getpass
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add parent directory to path to import schwab_api
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import schwab_api modules
from schwab_api.core import SchwabAPI
from schwab_api.config.settings import SettingsManager
from schwab_api.config.secure_storage import SecureStorage
from schwab_api.auth.oauth.oauth_client import OAuthClient
from schwab_api.auth.oauth.token_manager import TokenManager
from schwab_api.auth.oauth.callback_server import CallbackServer
from config.config_manager import ConfigManager, config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('oauth_demo')


def setup_configuration(config_file: Optional[str] = None) -> tuple:
    """
    Set up configuration and storage
    
    Args:
        config_file: Optional path to JSON config file
    
    Returns:
        Tuple of (settings_manager, secure_storage)
    """
    # Create config directory if it doesn't exist
    base_dir = Path(__file__).resolve().parent.parent
    config_dir = base_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Initialize settings manager with integration to ConfigManager
    settings = SettingsManager(
        config_path=config_file,
        config_manager_instance=config_manager
    )
    
    # Initialize secure storage
    storage_dir = settings.get('security', 'secure_storage_dir')
    if not os.path.isabs(storage_dir):
        storage_dir = base_dir / storage_dir
    storage = SecureStorage(str(storage_dir))
    
    return settings, storage


def setup_oauth(settings: SettingsManager, storage: SecureStorage, api_type: str = 'market_data') -> OAuthClient:
    """
    Set up OAuth components
    
    Args:
        settings: Settings manager instance
        storage: Secure storage instance
        api_type: API type ('market_data' or 'accounts_trading')
    
    Returns:
        OAuthClient instance
    """
    # Initialize token manager
    token_manager = TokenManager(storage, api_type, settings)
    
    # Initialize callback server
    callback_server = CallbackServer()
    
    # Initialize OAuth client (credentials come from settings)
    oauth_client = OAuthClient(
        api_type,
        settings,
        token_manager,
        callback_server
    )
    
    return oauth_client


def authenticate_and_get_quotes(oauth_client: OAuthClient, symbols: List[str]) -> Optional[Dict[str, Any]]:
    """
    Authenticate and get quotes for symbols
    
    Args:
        oauth_client: OAuth client instance
        symbols: List of symbols to get quotes for
    
    Returns:
        Dictionary of quote data or None if failed
    """
    # Initialize the API client
    api = SchwabAPI(oauth_client)
    
    # Authenticate
    print("Authenticating with Schwab API...")
    if not api.authenticate():
        print("Authentication failed. Please check your credentials.")
        return None
    
    print("Authentication successful!")
    
    # Display authentication status
    auth_status = api.get_auth_status()
    print(f"Authentication status: {auth_status['authenticated']}")
    print(f"Token expires in: {auth_status['token_info'].get('expires_in', 'unknown')} seconds")
    
    # Get quotes
    print(f"Getting quotes for {symbols}...")
    try:
        quotes = api.get_quotes(symbols)
        return quotes
    except Exception as e:
        print(f"Error getting quotes: {str(e)}")
        return None


def save_credentials(client_id: str, client_secret: str) -> None:
    """
    Save credentials to .env file
    
    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
    """
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / "config" / ".env"
    
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
    
    print(f"Credentials saved to {env_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Schwab API OAuth Demo')
    parser.add_argument('--save-credentials', action='store_true', help='Save credentials to .env file')
    parser.add_argument('--symbols', type=str, default='AAPL,MSFT,GOOGL', help='Comma-separated list of symbols')
    args = parser.parse_args()
    
    print("Schwab API OAuth Demo")
    print("=====================")
    
    # Set up configuration
    settings, storage = setup_configuration()
    
    # Check for existing credentials
    oauth_config = config_manager.get_schwab_oauth_config()
    client_id = oauth_config.get('client_id')
    client_secret = oauth_config.get('client_secret')
    
    # If no credentials or save requested, prompt for them
    if not client_id or not client_secret or args.save_credentials:
        print("Schwab API credentials required.")
        client_id = input("Enter your Schwab API client ID: ")
        client_secret = getpass.getpass("Enter your Schwab API client secret: ")
        
        if not client_id or not client_secret:
            print("Client ID and secret are required.")
            return
        
        if args.save_credentials:
            save_credentials(client_id, client_secret)
            # Reload configuration
            config_manager.load_env_file()
    
    # Set up OAuth client
    oauth_client = setup_oauth(settings, storage)
    
    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    # Authenticate and get quotes
    quotes = authenticate_and_get_quotes(oauth_client, symbols)
    
    # Display results
    if quotes:
        print("\nQuotes:")
        print(json.dumps(quotes, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDemo aborted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"\nError: {str(e)}")