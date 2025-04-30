@echo off
REM Script to run the Schwab API OAuth example in automated mode
REM This uses the mock implementation to demonstrate the OAuth flow

echo Schwab API OAuth Example (Automated Mode)
echo =======================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.10 or higher.
    goto :eof
)

echo Checking for required packages...
pip show requests >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install requests
    if %ERRORLEVEL% NEQ 0 (
        echo Error installing packages. Please check your Python installation.
        goto :eof
    )
)

echo.
echo Running Mock Schwab API OAuth Demo...
echo.

REM Create examples directory if it doesn't exist
if not exist "examples" (
    mkdir examples
)

REM Create the mock OAuth demo script
echo Creating mock OAuth demo script...
echo import os > examples\mock_oauth_demo.py
echo import json >> examples\mock_oauth_demo.py
echo import time >> examples\mock_oauth_demo.py
echo import logging >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo # Configure logging >> examples\mock_oauth_demo.py
echo logging.basicConfig( >> examples\mock_oauth_demo.py
echo     level=logging.INFO, >> examples\mock_oauth_demo.py
echo     format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s' >> examples\mock_oauth_demo.py
echo ) >> examples\mock_oauth_demo.py
echo logger = logging.getLogger('mock_oauth_demo') >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo class MockOAuthClient: >> examples\mock_oauth_demo.py
echo     """Mock OAuth client for demonstration purposes.""" >> examples\mock_oauth_demo.py
echo     def __init__(self, api_type): >> examples\mock_oauth_demo.py
echo         self.api_type = api_type >> examples\mock_oauth_demo.py
echo         self.authenticated = False >> examples\mock_oauth_demo.py
echo         self.token = None >> examples\mock_oauth_demo.py
echo         self.token_expiry = None >> examples\mock_oauth_demo.py
echo         logger.info(f"Initialized mock OAuth client for {api_type}") >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     def authenticate(self): >> examples\mock_oauth_demo.py
echo         """Simulate OAuth authentication.""" >> examples\mock_oauth_demo.py
echo         logger.info("Performing mock authentication") >> examples\mock_oauth_demo.py
echo         # Simulate authentication process >> examples\mock_oauth_demo.py
echo         self.authenticated = True >> examples\mock_oauth_demo.py
echo         self.token = "mock_access_token_" + str(int(time.time())) >> examples\mock_oauth_demo.py
echo         self.token_expiry = time.time() + 3600  # Token valid for 1 hour >> examples\mock_oauth_demo.py
echo         return True >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     def get_auth_status(self): >> examples\mock_oauth_demo.py
echo         """Get authentication status.""" >> examples\mock_oauth_demo.py
echo         return { >> examples\mock_oauth_demo.py
echo             "authenticated": self.authenticated, >> examples\mock_oauth_demo.py
echo             "api_type": self.api_type, >> examples\mock_oauth_demo.py
echo             "auth_method": "oauth", >> examples\mock_oauth_demo.py
echo             "token_status": "valid" if self.authenticated else "invalid", >> examples\mock_oauth_demo.py
echo             "token_expires_in": int(self.token_expiry - time.time()) if self.authenticated else 0 >> examples\mock_oauth_demo.py
echo         } >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo class MockSchwabAPIClient: >> examples\mock_oauth_demo.py
echo     """Mock Schwab API client for demonstration purposes.""" >> examples\mock_oauth_demo.py
echo     def __init__(self, api_type): >> examples\mock_oauth_demo.py
echo         self.api_type = api_type >> examples\mock_oauth_demo.py
echo         self.oauth_client = MockOAuthClient(api_type) >> examples\mock_oauth_demo.py
echo         logger.info(f"Initialized mock Schwab API client for {api_type}") >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     def authenticate(self): >> examples\mock_oauth_demo.py
echo         """Authenticate with the Schwab API.""" >> examples\mock_oauth_demo.py
echo         return self.oauth_client.authenticate() >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     def get_quotes(self, symbols): >> examples\mock_oauth_demo.py
echo         """Get quotes for the specified symbols.""" >> examples\mock_oauth_demo.py
echo         logger.info(f"Getting mock quotes for {symbols}") >> examples\mock_oauth_demo.py
echo         if not self.oauth_client.authenticated: >> examples\mock_oauth_demo.py
echo             raise Exception("Not authenticated") >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo         # Generate mock quotes >> examples\mock_oauth_demo.py
echo         quotes = {} >> examples\mock_oauth_demo.py
echo         for symbol in symbols: >> examples\mock_oauth_demo.py
echo             quotes[symbol] = { >> examples\mock_oauth_demo.py
echo                 "symbol": symbol, >> examples\mock_oauth_demo.py
echo                 "description": f"{symbol} Inc.", >> examples\mock_oauth_demo.py
echo                 "lastPrice": 174.25, >> examples\mock_oauth_demo.py
echo                 "change": 2.5, >> examples\mock_oauth_demo.py
echo                 "percentChange": 1.75, >> examples\mock_oauth_demo.py
echo                 "open": 148.5, >> examples\mock_oauth_demo.py
echo                 "high": 152.75, >> examples\mock_oauth_demo.py
echo                 "low": 147.8, >> examples\mock_oauth_demo.py
echo                 "volume": 5000000, >> examples\mock_oauth_demo.py
echo                 "timestamp": time.strftime("%%Y-%%m-%%dT%%H:%%M:%%S.%%f")[:-3] >> examples\mock_oauth_demo.py
echo             } >> examples\mock_oauth_demo.py
echo         return quotes >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo def main(): >> examples\mock_oauth_demo.py
echo     """Run the mock OAuth demo.""" >> examples\mock_oauth_demo.py
echo     print("Mock Schwab API OAuth Demo") >> examples\mock_oauth_demo.py
echo     print("=========================\n") >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     print("Initializing mock OAuth client...") >> examples\mock_oauth_demo.py
echo     client = MockSchwabAPIClient("market_data") >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     print("\nAuthenticating with mock Schwab API...") >> examples\mock_oauth_demo.py
echo     client.authenticate() >> examples\mock_oauth_demo.py
echo     print("Authentication successful!") >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     # Get authentication status >> examples\mock_oauth_demo.py
echo     auth_status = client.oauth_client.get_auth_status() >> examples\mock_oauth_demo.py
echo     print(f"Authentication status: {auth_status['authenticated']}") >> examples\mock_oauth_demo.py
echo     print(f"API type: {auth_status['api_type']}") >> examples\mock_oauth_demo.py
echo     print(f"Auth method: {auth_status['auth_method']}") >> examples\mock_oauth_demo.py
echo     print(f"Token status: {auth_status['token_status']}") >> examples\mock_oauth_demo.py
echo     print(f"Token expires in: {auth_status['token_expires_in']} seconds\n") >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     # Get quotes >> examples\mock_oauth_demo.py
echo     symbols = ["AAPL", "MSFT", "GOOGL"] >> examples\mock_oauth_demo.py
echo     print(f"Getting quotes for {symbols}...") >> examples\mock_oauth_demo.py
echo     quotes = client.get_quotes(symbols) >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     print("\nQuotes:") >> examples\mock_oauth_demo.py
echo     print(json.dumps(quotes, indent=2)) >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo     print("\nDemo completed successfully.") >> examples\mock_oauth_demo.py
echo. >> examples\mock_oauth_demo.py
echo if __name__ == "__main__": >> examples\mock_oauth_demo.py
echo     main() >> examples\mock_oauth_demo.py

echo.
echo Running mock OAuth demo...
python examples\mock_oauth_demo.py

echo.
echo Demo completed.
echo.

pause