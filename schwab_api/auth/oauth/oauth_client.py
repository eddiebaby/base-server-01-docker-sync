"""
OAuth Client for Schwab API

This module implements OAuth authentication for the Schwab API.
"""

import os
import time
import logging
import webbrowser
import requests
import base64
from typing import Dict, Optional, Any, Tuple

from ..auth_manager import AuthenticationManager
from ..exceptions import AuthenticationError, TokenError, CallbackError, NetworkError
from .token_manager import TokenManager
from .callback_server import CallbackServer

# Configure logging
logger = logging.getLogger('schwab_api.oauth.client')


class OAuthClient(AuthenticationManager):
    """
    OAuth2 implementation for Schwab API authentication.
    
    This class implements the OAuth2 authorization flow for the Schwab API,
    including authorization code flow, token refresh, and authentication state
    management.
    """
    
    def __init__(
        self,
        api_type: str,
        settings_manager: Any,
        token_manager: TokenManager,
        callback_server: Optional[CallbackServer] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Initialize the OAuth client.
        
        Args:
            api_type (str): API type ('market_data' or 'accounts_trading')
            settings_manager (Any): Settings manager instance
            token_manager (TokenManager): Token manager instance
            callback_server (Optional[CallbackServer]): Callback server instance
            client_id (Optional[str]): OAuth client ID (if not using settings manager)
            client_secret (Optional[str]): OAuth client secret (if not using settings manager)
        """
        self._api_type = api_type
        self.settings = settings_manager
        self.token_manager = token_manager
        self.callback_server = callback_server or CallbackServer()
        
        # Get credentials from settings if not provided
        credentials = self.settings.get_oauth_client_credentials()
        self.client_id = client_id or credentials.get('client_id')
        self.client_secret = client_secret or credentials.get('client_secret')
        
        if not self.client_id or not self.client_secret:
            logger.warning("Schwab API OAuth client credentials not configured")
        
        # Get API URLs from settings
        self.token_url = self.settings.get_oauth_token_url()
        self.auth_url = self.settings.get_oauth_authorize_url()
        self.callback_url = self.settings.get_callback_url(api_type)
    
    @property
    def api_type(self) -> str:
        """
        Get the API type this authentication is for.
        
        Returns:
            str: API type (e.g., 'market_data', 'accounts_trading')
        """
        return self._api_type
        
    @property
    def auth_method(self) -> str:
        """
        Get the authentication method name.
        
        Returns:
            str: Authentication method name (e.g., 'oauth', 'api_key')
        """
        return 'oauth'
    
    def authenticate(self) -> bool:
        """
        Authenticate with Schwab API using OAuth flow.
        
        This method handles the complete OAuth flow, including:
        1. Checking for existing valid tokens
        2. Refreshing tokens if needed
        3. Starting the full OAuth flow if necessary
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            # Check if we already have a valid token
            if self.is_authenticated():
                logger.info(f"Already authenticated for {self.api_type}")
                return True
                
            # Try to refresh token if we have a refresh token
            if self.token_manager.refresh_token:
                try:
                    logger.info("Attempting to refresh token")
                    self.refresh_auth()
                    logger.info("Token refresh successful")
                    return True
                except TokenError as e:
                    logger.warning(f"Token refresh failed: {str(e)}")
                    # Continue with full auth flow
            
            # Start full OAuth flow
            logger.info("Starting full OAuth authentication flow")
            return self._start_oauth_flow()
            
        except AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return False
    
    def is_authenticated(self) -> bool:
        """
        Check if current authentication is valid.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        # Use token manager to check if token is valid
        buffer_seconds = self.settings.get('auth', 'token_refresh_buffer_seconds', 300)
        return self.token_manager.is_token_valid(buffer_seconds)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dict[str, str]: Headers to include in API requests
        
        Raises:
            AuthenticationError: If not authenticated
        """
        try:
            if not self.is_authenticated():
                # Try to refresh token
                if self.token_manager.refresh_token:
                    self.refresh_auth()
                else:
                    raise AuthenticationError("Not authenticated and no refresh token available")
            
            # Get authorization header
            return self.token_manager.get_auth_header()
            
        except Exception as e:
            logger.error(f"Error getting auth headers: {str(e)}")
            raise AuthenticationError(f"Error getting auth headers: {str(e)}")
    
    def refresh_auth(self) -> bool:
        """
        Refresh authentication credentials.
        
        Returns:
            bool: True if refresh was successful, False otherwise
        """
        try:
            # Use token manager to refresh access token
            return self.token_manager.refresh_access_token(
                self.client_id,
                self.client_secret,
                self.token_url
            )
        except Exception as e:
            logger.error(f"Error refreshing authentication: {str(e)}")
            raise AuthenticationError(f"Error refreshing authentication: {str(e)}")
    
    def _get_authorization_url(self, state: str) -> str:
        """
        Build OAuth authorization URL.
        
        Args:
            state (str): CSRF state token
            
        Returns:
            str: Authorization URL with parameters
        """
        # Build authorization URL with parameters
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.callback_url,
            'response_type': 'code',
            'state': state
        }
        
        # Convert params to query string
        query = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        return f"{self.auth_url}?{query}"
    
    def _start_oauth_flow(self) -> bool:
        """
        Start the full OAuth flow with browser authorization.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Start callback server
            actual_callback_url, state = self.callback_server.start()
            
            # Get authorization URL
            auth_url = self._get_authorization_url(state)
            logger.info(f"Opening browser for authorization: {auth_url}")
            
            # Open browser for user authorization
            webbrowser.open(auth_url)
            
            # Wait for callback with timeout
            timeout = self.settings.get('auth', 'auth_timeout_seconds', 300)
            callback_data = self.callback_server.wait_for_callback(timeout)
            
            # Stop the callback server
            self.callback_server.stop()
            
            # Check if we got a callback
            if not callback_data:
                logger.error("No callback received (timed out)")
                return False
                
            # Check for error in callback
            if 'error' in callback_data:
                error_msg = f"Authorization error: {callback_data.get('error', 'Unknown error')}"
                if 'error_description' in callback_data:
                    error_msg += f" - {callback_data['error_description']}"
                logger.error(error_msg)
                return False
                
            # Check for authorization code
            if 'code' not in callback_data:
                logger.error("No authorization code in callback")
                return False
                
            # Exchange code for tokens
            auth_code = callback_data['code']
            return self._exchange_code_for_token(auth_code)
            
        except CallbackError as e:
            logger.error(f"Callback error: {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"Error in OAuth flow: {str(e)}")
            return False
            
        finally:
            # Ensure callback server is stopped
            try:
                self.callback_server.stop()
            except:
                pass
    
    def _exchange_code_for_token(self, auth_code: str) -> bool:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            auth_code (str): Authorization code from callback
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Exchanging authorization code for tokens")
        
        # Prepare the request
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.callback_url
        }
        
        try:
            response = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                timeout=self.settings.get('network', 'request_timeout_seconds', 30)
            )
            
            if response.status_code == 200:
                # Parse token response
                token_data = response.json()
                
                # Extract tokens
                access_token = token_data.get('access_token')
                refresh_token = token_data.get('refresh_token')
                expires_in = token_data.get('expires_in', 3600)
                
                if not access_token:
                    logger.error("No access token in response")
                    return False
                    
                # Save tokens
                self.token_manager.save_tokens(access_token, refresh_token, expires_in)
                
                logger.info("Token exchange successful")
                return True
            else:
                error_msg = f"Token exchange failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', '')}: {error_data.get('error_description', '')}"
                except:
                    error_msg += f" - {response.text}"
                    
                logger.error(error_msg)
                return False
                
        except requests.RequestException as e:
            logger.error(f"Network error during token exchange: {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            return False
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get information about the current token.
        
        Returns:
            Dict[str, Any]: Token information
        """
        return self.token_manager.get_token_info()
    
    def revoke_tokens(self) -> bool:
        """
        Revoke current tokens.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.token_manager.clear_tokens()