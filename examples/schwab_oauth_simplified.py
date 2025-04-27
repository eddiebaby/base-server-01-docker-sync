#!/usr/bin/env python
"""
Simplified Schwab API OAuth Authentication Example
:TechnologyVersion Python 3.10+
:AuthenticationPattern OAuth2
:SecurityPattern for credentials management

This script demonstrates the simplified integration for Schwab API OAuth authentication
using the SchwabOAuthIntegration module. It shows the recommended approach for
implementing Schwab API authentication in your applications.
"""

import sys
import json
import logging
import argparse
import getpass
from pathlib import Path

# Add parent directory to path to import schwab_api
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import Schwab API modules
from schwab_api.core import SchwabAPI
from schwab_api.auth.oauth_integration import SchwabOAuthIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('schwab_oauth_example')


def fetch_market_data(api_client: SchwabAPI, symbols: list) -> None:
    """
    Fetch and display market data for the specified symbols
    
    Args:
        api_client: Initialized Schwab API client
        symbols: List of stock symbols to fetch data for
    """
    try:
        # Get quotes for symbols
        print(f"\nFetching market data for {symbols}...")
        quotes = api_client.get_quotes(symbols)
        
        if quotes:
            print("\nQuotes data:")
            print(json.dumps(quotes, indent=2))
        else:
            print("No quote data returned")
    
    except Exception as e:
        print(f"Error fetching market data: {str(e)}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Simplified Schwab API OAuth Example')
    parser.add_argument('--save-credentials', action='store_true', help='Save credentials to .env file')
    parser.add_argument('--symbols', type=str, default='AAPL,MSFT,GOOGL', help='Comma-separated list of symbols')
    parser.add_argument('--api-type', type=str, default='market_data', choices=['market_data', 'accounts_trading'],
                        help='API type to authenticate with')
    args = parser.parse_args()
    
    print("Simplified Schwab API OAuth Example")
    print("===================================")
    
    # If save-credentials flag is set, prompt for credentials and save them
    if args.save_credentials:
        print("\nSetting up Schwab API credentials")
        client_id = input("Enter your Schwab API client ID: ")
        client_secret = getpass.getpass("Enter your Schwab API client secret: ")
        
        if not client_id or not client_secret:
            print("Error: Client ID and secret are required")
            return
        
        # Save credentials
        if SchwabOAuthIntegration.save_credentials(client_id, client_secret):
            print("Credentials saved successfully")
        else:
            print("Error saving credentials")
            return
    
    # Create OAuth integration (using default configuration)
    print(f"\nInitializing Schwab API OAuth integration for {args.api_type} API...")
    oauth_integration = SchwabOAuthIntegration.create_default_instance(api_type=args.api_type)
    
    # Check if already authenticated
    if oauth_integration.check_authentication():
        token_info = oauth_integration.get_token_info()
        print("Already authenticated")
        print(f"Token status: {token_info.get('status', 'unknown')}")
        print(f"Token expires in: {token_info.get('expires_in', 'unknown')} seconds")
    else:
        print("Not authenticated. Starting authentication flow...")
    
    # Create Schwab API client using the OAuth client
    oauth_client = oauth_integration.get_oauth_client()
    api_client = SchwabAPI(oauth_client)
    
    # Authenticate
    print("\nAuthenticating with Schwab API...")
    if not api_client.authenticate():
        print("Authentication failed. Please check your credentials.")
        return
    
    print("Authentication successful!")
    
    # Display authentication status
    auth_status = api_client.get_auth_status()
    print(f"Authentication status: {auth_status['authenticated']}")
    print(f"API type: {auth_status['api_type']}")
    print(f"Auth method: {auth_status['auth_method']}")
    print(f"Token status: {auth_status['token_info'].get('status', 'unknown')}")
    print(f"Token expires in: {auth_status['token_info'].get('expires_in', 'unknown')} seconds")
    
    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    # Fetch market data
    fetch_market_data(api_client, symbols)
    
    print("\nExample completed. You can now integrate Schwab API in your applications.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExample aborted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"\nError: {str(e)}")