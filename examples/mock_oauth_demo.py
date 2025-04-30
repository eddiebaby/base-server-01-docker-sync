import os 
import json 
import time 
import logging 
 
# Configure logging 
logging.basicConfig( 
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' 
) 
logger = logging.getLogger('mock_oauth_demo') 
 
class MockOAuthClient: 
    """Mock OAuth client for demonstration purposes.""" 
    def __init__(self, api_type): 
        self.api_type = api_type 
        self.authenticated = False 
        self.token = None 
        self.token_expiry = None 
        logger.info(f"Initialized mock OAuth client for {api_type}") 
 
    def authenticate(self): 
        """Simulate OAuth authentication.""" 
        logger.info("Performing mock authentication") 
        # Simulate authentication process 
        self.authenticated = True 
        self.token = "mock_access_token_" + str(int(time.time())) 
        self.token_expiry = time.time() + 3600  # Token valid for 1 hour 
        return True 
 
    def get_auth_status(self): 
        """Get authentication status.""" 
        return { 
            "authenticated": self.authenticated, 
            "api_type": self.api_type, 
            "auth_method": "oauth", 
            "token_status": "valid" if self.authenticated else "invalid", 
            "token_expires_in": int(self.token_expiry - time.time()) if self.authenticated else 0 
        } 
 
class MockSchwabAPIClient: 
    """Mock Schwab API client for demonstration purposes.""" 
    def __init__(self, api_type): 
        self.api_type = api_type 
        self.oauth_client = MockOAuthClient(api_type) 
        logger.info(f"Initialized mock Schwab API client for {api_type}") 
 
    def authenticate(self): 
        """Authenticate with the Schwab API.""" 
        return self.oauth_client.authenticate() 
 
    def get_quotes(self, symbols): 
        """Get quotes for the specified symbols.""" 
        logger.info(f"Getting mock quotes for {symbols}") 
        if not self.oauth_client.authenticated: 
            raise Exception("Not authenticated") 
 
        # Generate mock quotes 
        quotes = {} 
        for symbol in symbols: 
            quotes[symbol] = { 
                "symbol": symbol, 
                "description": f"{symbol} Inc.", 
                "lastPrice": 174.25, 
                "change": 2.5, 
                "percentChange": 1.75, 
                "open": 148.5, 
                "high": 152.75, 
                "low": 147.8, 
                "volume": 5000000, 
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] 
            } 
        return quotes 
 
def main(): 
    """Run the mock OAuth demo.""" 
    print("Mock Schwab API OAuth Demo") 
    print("=========================\n") 
 
    print("Initializing mock OAuth client...") 
    client = MockSchwabAPIClient("market_data") 
 
    print("\nAuthenticating with mock Schwab API...") 
    client.authenticate() 
    print("Authentication successful!") 
 
    # Get authentication status 
    auth_status = client.oauth_client.get_auth_status() 
    print(f"Authentication status: {auth_status['authenticated']}") 
    print(f"API type: {auth_status['api_type']}") 
    print(f"Auth method: {auth_status['auth_method']}") 
    print(f"Token status: {auth_status['token_status']}") 
    print(f"Token expires in: {auth_status['token_expires_in']} seconds\n") 
 
    # Get quotes 
    symbols = ["AAPL", "MSFT", "GOOGL"] 
    print(f"Getting quotes for {symbols}...") 
    quotes = client.get_quotes(symbols) 
 
    print("\nQuotes:") 
    print(json.dumps(quotes, indent=2)) 
 
    print("\nDemo completed successfully.") 
 
if __name__ == "__main__": 
    main() 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' 
) 
logger = logging.getLogger('mock_oauth_demo') 
 
class MockOAuthClient: 
    """Mock OAuth client for demonstration purposes.""" 
    def __init__(self, api_type): 
        self.api_type = api_type 
        self.authenticated = False 
        self.token = None 
        self.token_expiry = None 
        logger.info(f"Initialized mock OAuth client for {api_type}") 
 
    def authenticate(self): 
        """Simulate OAuth authentication.""" 
        logger.info("Performing mock authentication") 
        # Simulate authentication process 
        self.authenticated = True 
        self.token = "mock_access_token_" + str(int(time.time())) 
        self.token_expiry = time.time() + 3600  # Token valid for 1 hour 
        return True 
 
    def get_auth_status(self): 
        """Get authentication status.""" 
        return { 
            "authenticated": self.authenticated, 
            "api_type": self.api_type, 
            "auth_method": "oauth", 
            "token_status": "valid" if self.authenticated else "invalid", 
            "token_expires_in": int(self.token_expiry - time.time()) if self.authenticated else 0 
        } 
 
class MockSchwabAPIClient: 
    """Mock Schwab API client for demonstration purposes.""" 
    def __init__(self, api_type): 
        self.api_type = api_type 
        self.oauth_client = MockOAuthClient(api_type) 
        logger.info(f"Initialized mock Schwab API client for {api_type}") 
 
    def authenticate(self): 
        """Authenticate with the Schwab API.""" 
        return self.oauth_client.authenticate() 
 
    def get_quotes(self, symbols): 
        """Get quotes for the specified symbols.""" 
        logger.info(f"Getting mock quotes for {symbols}") 
        if not self.oauth_client.authenticated: 
            raise Exception("Not authenticated") 
 
        # Generate mock quotes 
        quotes = {} 
        for symbol in symbols: 
            quotes[symbol] = { 
                "symbol": symbol, 
                "description": f"{symbol} Inc.", 
                "lastPrice": 174.25, 
                "change": 2.5, 
                "percentChange": 1.75, 
                "open": 148.5, 
                "high": 152.75, 
                "low": 147.8, 
                "volume": 5000000, 
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] 
            } 
        return quotes 
 
def main(): 
    """Run the mock OAuth demo.""" 
    print("Mock Schwab API OAuth Demo") 
    print("=========================\n") 
 
    print("Initializing mock OAuth client...") 
    client = MockSchwabAPIClient("market_data") 
 
    print("\nAuthenticating with mock Schwab API...") 
    client.authenticate() 
    print("Authentication successful!") 
 
    # Get authentication status 
    auth_status = client.oauth_client.get_auth_status() 
    print(f"Authentication status: {auth_status['authenticated']}") 
    print(f"API type: {auth_status['api_type']}") 
    print(f"Auth method: {auth_status['auth_method']}") 
    print(f"Token status: {auth_status['token_status']}") 
    print(f"Token expires in: {auth_status['token_expires_in']} seconds\n") 
 
    # Get quotes 
    symbols = ["AAPL", "MSFT", "GOOGL"] 
    print(f"Getting quotes for {symbols}...") 
    quotes = client.get_quotes(symbols) 
 
    print("\nQuotes:") 
    print(json.dumps(quotes, indent=2)) 
 
    print("\nDemo completed successfully.") 
 
if __name__ == "__main__": 
    main() 
