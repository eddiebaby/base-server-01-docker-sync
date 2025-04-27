#!/usr/bin/env python
"""
Schwab API Credentials Setup Utility
:TechnologyVersion Python 3.10+
:SecurityPattern for credentials management

This script helps you set up your Schwab API credentials for authentication.
It guides you through the process and securely stores your credentials in the .env file.
"""

import os
import sys
import getpass
from pathlib import Path

# Add parent directories to path to import schwab_api
base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(base_dir))

from schwab_api.auth.oauth_integration import SchwabOAuthIntegration


def clear_screen():
    """Clear the console screen based on the OS"""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_header():
    """Display the script header"""
    print("=" * 70)
    print("Schwab API Credentials Setup".center(70))
    print("=" * 70)
    print("\nThis utility will help you set up your Schwab API credentials.")
    print("These credentials are required to authenticate with the Schwab API.")
    print("\nYour credentials will be stored securely in the .env file.")
    print("They will NOT be hardcoded in the source code.")
    print("=" * 70)
    print()


def verify_directory_structure():
    """Verify that the directory structure exists"""
    config_dir = base_dir / "config"
    if not config_dir.exists():
        print(f"Creating config directory at {config_dir}")
        config_dir.mkdir(exist_ok=True)
    
    env_file = config_dir / ".env"
    if not env_file.exists():
        print(f"Creating .env file at {env_file}")
        with open(env_file, 'w') as f:
            f.write("# Schwab API Credentials\n")
    
    return config_dir, env_file


def get_current_credentials():
    """Get current Schwab API credentials if they exist"""
    env_file = base_dir / "config" / ".env"
    if not env_file.exists():
        return None, None
    
    client_id = None
    client_secret = None
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('SCHWAB_CLIENT_ID='):
                client_id = line.strip().split('=', 1)[1]
            elif line.startswith('SCHWAB_CLIENT_SECRET='):
                client_secret = line.strip().split('=', 1)[1]
    
    return client_id, client_secret


def get_schwab_api_endpoints():
    """Get current Schwab API endpoints if they exist"""
    env_file = base_dir / "config" / ".env"
    if not env_file.exists():
        return None, None, None
    
    base_url = None
    auth_url = None
    token_url = None
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('SCHWAB_API_BASE_URL='):
                base_url = line.strip().split('=', 1)[1]
            elif line.startswith('SCHWAB_AUTH_URL='):
                auth_url = line.strip().split('=', 1)[1]
            elif line.startswith('SCHWAB_TOKEN_URL='):
                token_url = line.strip().split('=', 1)[1]
    
    return base_url, auth_url, token_url


def save_credentials(client_id, client_secret, base_url=None, auth_url=None, token_url=None):
    """Save credentials to .env file"""
    # First save the client ID and secret using the integration class
    success = SchwabOAuthIntegration.save_credentials(client_id, client_secret)
    
    if not success:
        print("Error saving credentials. Please try again.")
        return False
    
    # Now update the endpoints if provided
    if base_url or auth_url or token_url:
        env_file = base_dir / "config" / ".env"
        
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Check for existing lines
        has_base_url = any(line.startswith('SCHWAB_API_BASE_URL=') for line in lines)
        has_auth_url = any(line.startswith('SCHWAB_AUTH_URL=') for line in lines)
        has_token_url = any(line.startswith('SCHWAB_TOKEN_URL=') for line in lines)
        
        # Update or add lines
        if base_url:
            if has_base_url:
                lines = [f"SCHWAB_API_BASE_URL={base_url}\n" if line.startswith('SCHWAB_API_BASE_URL=') else line for line in lines]
            else:
                lines.append(f"SCHWAB_API_BASE_URL={base_url}\n")
        
        if auth_url:
            if has_auth_url:
                lines = [f"SCHWAB_AUTH_URL={auth_url}\n" if line.startswith('SCHWAB_AUTH_URL=') else line for line in lines]
            else:
                lines.append(f"SCHWAB_AUTH_URL={auth_url}\n")
                
        if token_url:
            if has_token_url:
                lines = [f"SCHWAB_TOKEN_URL={token_url}\n" if line.startswith('SCHWAB_TOKEN_URL=') else line for line in lines]
            else:
                lines.append(f"SCHWAB_TOKEN_URL={token_url}\n")
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
    
    return True


def setup_credentials():
    """Main function to set up credentials"""
    clear_screen()
    show_header()
    
    # Verify directory structure
    config_dir, env_file = verify_directory_structure()
    print(f"Using config directory: {config_dir}")
    print(f"Using .env file: {env_file}")
    print()
    
    # Get current credentials if they exist
    current_client_id, current_client_secret = get_current_credentials()
    current_base_url, current_auth_url, current_token_url = get_schwab_api_endpoints()
    
    # Display current credentials if they exist
    if current_client_id and current_client_secret:
        print("Current Schwab API credentials:")
        print(f"  Client ID: {current_client_id}")
        print(f"  Client Secret: {'*' * len(current_client_secret) if current_client_secret else None}")
        print()
    
    if current_base_url or current_auth_url or current_token_url:
        print("Current Schwab API endpoints:")
        print(f"  Base URL: {current_base_url}")
        print(f"  Auth URL: {current_auth_url}")
        print(f"  Token URL: {current_token_url}")
        print()
    
    # Ask if user wants to update credentials
    if current_client_id and current_client_secret:
        update = input("Do you want to update your Schwab API credentials? (y/n): ").lower()
        if update != 'y':
            print("Keeping existing credentials.")
            return
    
    # Get new credentials
    print("\nPlease enter your Schwab API credentials:")
    client_id = input("  Client ID: ").strip()
    client_secret = getpass.getpass("  Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("Error: Client ID and Client Secret are required.")
        return
    
    # Ask about API endpoints
    print("\nDo you want to configure Schwab API endpoints?")
    configure_endpoints = input("This is required for live API access (y/n): ").lower()
    
    base_url = None
    auth_url = None
    token_url = None
    
    if configure_endpoints == 'y':
        print("\nPlease enter the Schwab API endpoints (press Enter to keep current values):")
        
        base_url_prompt = f"  Base URL [{current_base_url or 'https://api.schwabapi.com/v1'}]: "
        base_url = input(base_url_prompt).strip() or current_base_url or 'https://api.schwabapi.com/v1'
        
        auth_url_prompt = f"  Auth URL [{current_auth_url or base_url + '/oauth/authorize'}]: "
        auth_url = input(auth_url_prompt).strip() or current_auth_url or base_url + '/oauth/authorize'
        
        token_url_prompt = f"  Token URL [{current_token_url or base_url + '/oauth/token'}]: "
        token_url = input(token_url_prompt).strip() or current_token_url or base_url + '/oauth/token'
    
    # Save credentials
    print("\nSaving credentials...")
    success = save_credentials(client_id, client_secret, base_url, auth_url, token_url)
    
    if success:
        print("Credentials saved successfully!")
        print("\nYou can now use the Schwab API with the following examples:")
        print("  - Run 'python examples/schwab_oauth_simplified.py' to test the OAuth flow")
        print("  - Run 'python examples/oauth_demo.py' for a more detailed example")
    else:
        print("Error saving credentials.")


if __name__ == "__main__":
    try:
        setup_credentials()
    except KeyboardInterrupt:
        print("\nSetup aborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)