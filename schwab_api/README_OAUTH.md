# Schwab API OAuth Authentication Implementation

This documentation provides details on the OAuth authentication implementation for Schwab API integration.

## Overview

The Schwab API OAuth implementation follows the official Schwab protocol as described at https://developer.schwab.com/user-guides/get-started/authenticate-with-oauth. It provides secure token management, proper credential storage, and a complete OAuth2 flow integration.

## Key Components

The implementation consists of the following key components:

1. **OAuth Client** (`schwab_api/auth/oauth/oauth_client.py`) - Implements the OAuth2 authorization flow
2. **Token Manager** (`schwab_api/auth/oauth/token_manager.py`) - Handles secure token storage and refresh
3. **Callback Server** (`schwab_api/auth/oauth/callback_server.py`) - Manages the OAuth callback process
4. **Secure Storage** (`schwab_api/config/secure_storage.py`) - Provides secure credential and token storage
5. **Settings Manager** (`schwab_api/config/settings.py`) - Manages API configuration
6. **OAuth Integration** (`schwab_api/auth/oauth_integration.py`) - High-level interface for using the OAuth components

## Secure Credential Management

API credentials (client ID and client secret) are managed securely through:

1. Environment variables (highest priority)
2. `.env` file in the config directory
3. Configuration files (lowest priority)

**Never hardcode credentials in your code.**

## Setup Guide

### Prerequisites

- Python 3.10 or higher
- Required packages are listed in `requirements.txt`
- Schwab API Developer Account with OAuth credentials

### Configuration

1. **Run the Setup Utility**

   The easiest way to configure the Schwab API credentials is to run the setup utility:

   ```
   setup_schwab_credentials.bat
   ```

   This utility will:
   - Guide you through the process of entering your Schwab API credentials
   - Allow you to configure API endpoints
   - Securely store your credentials in the `.env` file
   - Test the configuration

2. **Configure Environment Manually**

   Alternatively, you can manually create or edit the `.env` file in the config directory with your Schwab API credentials:

   ```
   SCHWAB_CLIENT_ID=your_client_id_here
   SCHWAB_CLIENT_SECRET=your_client_secret_here
   SCHWAB_REDIRECT_URI=http://localhost:8000/callback
   SCHWAB_API_BASE_URL=https://api.schwabapi.com/v1
   SCHWAB_AUTH_URL=https://api.schwabapi.com/v1/oauth/authorize
   SCHWAB_TOKEN_URL=https://api.schwabapi.com/v1/oauth/token
   ```

3. **Use the Helper Method in Code**

   ```python
   from schwab_api.auth.oauth_integration import SchwabOAuthIntegration
   
   SchwabOAuthIntegration.save_credentials(
       client_id="your_client_id_here",
       client_secret="your_client_secret_here"
   )
   ```

### Connecting to the Live Schwab API

To connect to the live Schwab API:

1. **Obtain Schwab API Credentials**
   - Sign up for a Schwab API developer account
   - Create an application and get your client ID and secret
   - Register your callback URL (typically http://localhost:8000/callback for development)

2. **Configure the Correct Endpoints**
   - Use the setup utility to enter the official Schwab API endpoints
   - Alternatively, set them in the `.env` file

3. **Test the Connection**
   - Run one of the example scripts: `run_oauth_example.bat`
   - The browser will open and redirect you to the Schwab login page
   - After authenticating, you will be redirected back to the application

## Usage Examples

### Basic Usage

```python
from schwab_api.auth.oauth_integration import SchwabOAuthIntegration
from schwab_api.core import SchwabAPI

# Create OAuth integration (uses credentials from .env or environment)
oauth_integration = SchwabOAuthIntegration.create_default_instance(api_type='market_data')

# Get OAuth client and create API client
oauth_client = oauth_integration.get_oauth_client()
api_client = SchwabAPI(oauth_client)

# Authenticate
if api_client.authenticate():
    print("Authentication successful")
    
    # Make API requests
    quotes = api_client.get_quotes(['AAPL', 'MSFT'])
    print(quotes)
else:
    print("Authentication failed")
```

### Token Management

The implementation automatically handles token refresh. You can also:

```python
# Check if authenticated
is_auth = oauth_integration.check_authentication()

# Get token info
token_info = oauth_integration.get_token_info()
print(f"Token expires in: {token_info.get('expires_in')} seconds")

# Revoke tokens
oauth_integration.revoke_tokens()
```

## Security Considerations

1. **Platform-specific Secure Storage**
   - On Windows, the implementation uses the Windows Data Protection API (DPAPI)
   - On other platforms, it uses application-specific encryption with system-derived keys

2. **Token Lifecycle**
   - Access tokens are short-lived and automatically refreshed when needed
   - Refresh tokens are securely stored

3. **CSRF Protection**
   - The OAuth flow includes CSRF protection with state parameters

4. **No Hardcoded Secrets**
   - All credentials are loaded from secure configuration sources

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify your Schwab API credentials are correct
   - Check that your redirect URI matches what's registered in your Schwab developer account
   - Ensure your account has the necessary permissions

2. **Token Refresh Failures**
   - Refresh tokens may expire after a certain period
   - You may need to re-authenticate with full flow

3. **Network Issues**
   - Check your internet connection
   - Verify the Schwab API service is available

### Logging

The implementation includes comprehensive logging. Set the logging level to DEBUG for more detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Example Applications

For example applications demonstrating the OAuth implementation:

1. `examples/oauth_demo.py` - Standard OAuth flow demonstration
2. `examples/schwab_oauth_simplified.py` - Simplified integration example

## Advanced Configuration

Advanced configuration options can be set in the server_config.json file in the config directory:

```json
{
  "schwab_oauth": {
    "scopes": "market_data accounts_trading",
    "auth_timeout_seconds": 600,
    "token_refresh_buffer_seconds": 300
  }
}
```

## More Information

For more information about the Schwab API:
- Official Schwab API Documentation: https://developer.schwab.com/
- OAuth Protocol: https://developer.schwab.com/user-guides/get-started/authenticate-with-oauth