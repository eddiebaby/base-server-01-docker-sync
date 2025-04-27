# Schwab API Market Data Integration

This directory contains modules for working with Schwab API Market Data endpoints.

## Features

The market data integration builds on the OAuth authentication system to provide:

- Market data retrieval (quotes, charts, options, etc.)
- Data transformation and normalization
- Historical data management
- Real-time data streaming (if supported by Schwab API)

## Implementation Status

- OAuth Authentication: ✅ Completed
- Quote Data: ✅ Basic implementation
- Historical Data: 🚧 Planned
- Options Data: 🚧 Planned
- Real-time Streaming: 🚧 Planned

## Usage Example

```python
from schwab_api.auth.oauth_integration import SchwabOAuthIntegration
from schwab_api.core import SchwabAPI

# Create OAuth integration
oauth_integration = SchwabOAuthIntegration.create_default_instance(api_type='market_data')

# Get OAuth client and create API client
oauth_client = oauth_integration.get_oauth_client()
api_client = SchwabAPI(oauth_client)

# Authenticate
if api_client.authenticate():
    # Get quotes
    quotes = api_client.get_quotes(['AAPL', 'MSFT', 'GOOGL'])
    print(quotes)
```

## Design Principles

- Clean separation of concerns
- Security-first approach
- Error handling and resilience
- Comprehensive testing
- Clear documentation