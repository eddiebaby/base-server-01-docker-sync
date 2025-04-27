"""
Core API interface for Schwab API

This module provides the main entry point for interacting with the Schwab API.
"""

import logging
import json
import requests
from typing import Dict, Any, Optional, List, Union

from .auth.auth_manager import AuthenticationManager
from .auth.exceptions import AuthenticationError, NetworkError

# Configure logging
logger = logging.getLogger('schwab_api.core')


class SchwabAPI:
    """
    Main interface for the Schwab API.
    
    This class serves as the primary entry point for interacting with the
    Schwab API. It handles authentication, API requests, and provides
    access to different API endpoints.
    """
    
    def __init__(self, auth_manager: AuthenticationManager, settings_manager: Optional[Any] = None):
        """
        Initialize the Schwab API client.
        
        Args:
            auth_manager (AuthenticationManager): Authentication manager
            settings_manager (Optional[Any]): Settings manager
        """
        self.auth_manager = auth_manager
        self.settings = settings_manager
        self.api_type = auth_manager.api_type
        
        # Initialize API modules
        self._initialize_modules()
        
        logger.info(f"Initialized Schwab API client for {self.api_type}")
    
    def _initialize_modules(self):
        """Initialize API modules based on API type"""
        if self.api_type == 'market_data':
            # Initialize market data module
            from .market_data.market_data_client import MarketDataClient
            self.market_data = MarketDataClient(self)
        elif self.api_type == 'accounts_trading':
            # Initialize accounts and trading modules
            # (These would be implemented in future versions)
            pass
    
    def authenticate(self) -> bool:
        """
        Authenticate with the Schwab API.
        
        Returns:
            bool: True if authentication is successful, False otherwise
        """
        try:
            result = self.auth_manager.authenticate()
            
            if result:
                logger.info(f"Successfully authenticated for {self.api_type}")
            else:
                logger.error(f"Authentication failed for {self.api_type}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            return False
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return self.auth_manager.is_authenticated()
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Make a request to the Schwab API.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint (relative to base URL)
            params (Optional[Dict[str, Any]]): Query parameters
            data (Optional[Dict[str, Any]]): Request body (for POST, PUT, etc.)
            headers (Optional[Dict[str, str]]): Additional headers
            retry_auth (bool): Whether to retry with re-authentication on 401
            
        Returns:
            Dict[str, Any]: API response
            
        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If there's a network error
            ValueError: If the API returns an error
        """
        if not self.is_authenticated() and retry_auth:
            # Try to authenticate
            if not self.authenticate():
                raise AuthenticationError("Not authenticated and authentication failed")
        
        # Get base URL from settings if available
        base_url = getattr(self.settings, 'get_api_url', lambda x: None)(self.api_type)
        if not base_url:
            if self.api_type == 'market_data':
                base_url = "https://api.schwabapi.com/v1/market-data"
            else:
                base_url = "https://api.schwabapi.com/v1/accounts"
        
        # Build full URL
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        # Get authentication headers
        auth_headers = self.auth_manager.get_auth_headers()
        
        # Merge with additional headers
        request_headers = {"Content-Type": "application/json"}
        request_headers.update(auth_headers)
        if headers:
            request_headers.update(headers)
        
        # Get timeout from settings if available
        timeout = 30  # Default timeout
        if hasattr(self.settings, 'get'):
            timeout = self.settings.get('network', 'request_timeout_seconds', 30)
        
        try:
            # Make the request
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                timeout=timeout
            )
            
            # Check for authentication error
            if response.status_code == 401 and retry_auth:
                logger.warning("Received 401 unauthorized, attempting to re-authenticate")
                
                # Re-authenticate
                if self.authenticate():
                    # Retry the request
                    return self.request(
                        method, endpoint, params, data, headers, retry_auth=False
                    )
                else:
                    raise AuthenticationError("Re-authentication failed")
            
            # Check for successful response
            if 200 <= response.status_code < 300:
                if response.headers.get('Content-Type', '').startswith('application/json'):
                    return response.json()
                return {"status": "success", "status_code": response.status_code, "text": response.text}
            
            # Handle error response
            error_msg = f"API error: {response.status_code}"
            error_data = {}
            
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', '')}: {error_data.get('error_description', '')}"
            except:
                error_msg += f" - {response.text}"
            
            logger.error(error_msg)
            raise ValueError(error_msg, response.status_code, error_data)
            
        except requests.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            raise NetworkError(error_msg)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the Schwab API.
        
        Args:
            endpoint (str): API endpoint
            params (Optional[Dict[str, Any]]): Query parameters
            
        Returns:
            Dict[str, Any]: API response
        """
        return self.request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the Schwab API.
        
        Args:
            endpoint (str): API endpoint
            data (Dict[str, Any]): Request body
            
        Returns:
            Dict[str, Any]: API response
        """
        return self.request('POST', endpoint, data=data)
    
    def get_quotes(self, symbols: Union[str, List[str]], fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Get quotes for specified symbols.
        
        Args:
            symbols (Union[str, List[str]]): Symbol or list of symbols
            fields (Optional[str]): Comma-separated list of fields to return
            
        Returns:
            Dict[str, Any]: Quote data keyed by symbol
        """
        if self.api_type != 'market_data':
            raise ValueError("This method is only available for market_data API type")
            
        # Convert list of symbols to comma-separated string
        if isinstance(symbols, list):
            symbols_str = ','.join(symbols)
        else:
            symbols_str = symbols
            
        # Prepare parameters
        params = {'symbols': symbols_str}
        if fields:
            params['fields'] = fields
            
        return self.get('quotes', params=params)
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        Get authentication status.
        
        Returns:
            Dict[str, Any]: Authentication status information
        """
        # Get token info if available
        token_info = {}
        if hasattr(self.auth_manager, 'get_token_info'):
            token_info = self.auth_manager.get_token_info()
            
        return {
            'authenticated': self.is_authenticated(),
            'api_type': self.api_type,
            'auth_method': self.auth_manager.auth_method,
            'token_info': token_info
        }