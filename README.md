# Schwab API Client

A modular Python client for interacting with Charles Schwab API with OAuth authentication support.

## Features

- **Modular Design**: Clean separation of concerns with well-defined interfaces
- **OAuth Authentication**: Complete OAuth 2.0 flow implementation
- **Secure Storage**: Cross-platform secure credential storage
- **Market Data**: Access to market data endpoints
- **Extensible**: Easy to add support for additional API endpoints
- **Developer-Friendly**: Clear documentation and examples

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/schwab-api-client.git
cd schwab-api-client

# Install the package
pip install -e .
```

## Quick Start

### Authentication

```python
from schwab_api.core import SchwabAPI
from schwab_api.config.settings import SettingsManager
from schwab_api.config.secure_storage import SecureStorage
from schwab_api.auth.oauth.oauth_client import OAuthClient
from schwab_api.auth.oauth.token_manager import TokenManager
from schwab_api.auth.oauth.callback_server import CallbackServer

# Set up configuration
settings = SettingsManager()
storage = SecureStorage("./config")

# Set up OAuth components
token_manager = TokenManager(storage, "market_data", settings)
callback_server = CallbackServer()

# Initialize OAuth client
oauth_client = OAuthClient(
    "market_data",
    "YOUR_CLIENT_ID",
    "YOUR_CLIENT_SECRET",
    settings,
    token_manager,
    callback_server
)

# Initialize API
api = SchwabAPI(oauth_client, settings)

# Authenticate (opens browser for OAuth flow if needed)
if api.authenticate():
    print("Authentication successful!")
else:
    print("Authentication failed")
```

### Getting Market Data

```python
# Get quotes for symbols
quotes = api.get_quotes(["AAPL", "MSFT", "GOOGL"])
print(quotes)

# Access market data specific methods
price_history = api.market_data.get_price_history("AAPL", period=10)
```

## Project Structure

```
schwab_api/
├── __init__.py           # Package initialization
├── core.py               # Core API interface
├── auth/                 # Authentication components
│   ├── __init__.py
│   ├── auth_manager.py   # Abstract authentication interface
│   ├── exceptions.py     # Authentication-related exceptions
│   └── oauth/            # OAuth implementation
│       ├── __init__.py
│       ├── oauth_client.py     # OAuth client
│       ├── token_manager.py    # Token management
│       └── callback_server.py  # OAuth callback server
├── config/               # Configuration components
│   ├── __init__.py
│   ├── secure_storage.py # Secure credential storage
│   └── settings.py       # Settings management
└── market_data/          # Market data components
    ├── __init__.py
    └── market_data_client.py # Market data access
```

## Secure Credential Storage

The library securely stores credentials and tokens:

- On Windows: Uses Windows Data Protection API (DPAPI)
- On macOS/Linux: Uses system-derived encryption keys

## OAuth Flow

1. Client requests authentication
2. If no valid tokens exist, browser opens for authentication
3. User logs in and authorizes the application
4. Authorization code is returned via callback
5. Code is exchanged for access and refresh tokens
6. Tokens are securely stored for future use
7. Subsequent requests use the stored access token
8. Expired tokens are automatically refreshed when possible

## Examples

Check the `examples/` directory for complete usage examples:

- `oauth_demo.py`: Demonstrates OAuth authentication and basic API usage

## Future Additions

- Account and trading API support
- Historical data analysis tools
- Portfolio management
- Order execution and management
- Real-time data streaming

## License

This project is licensed under the MIT License - see the LICENSE file for details.