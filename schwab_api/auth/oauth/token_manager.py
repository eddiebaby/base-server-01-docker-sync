"""
Token Manager for Schwab API OAuth

This module handles OAuth token storage, validation, and refresh operations.
"""

import time
import logging
import json
import base64
import requests
from typing import Dict, Any, Optional, Tuple

from ..exceptions import TokenError
from ...config.secure_storage import SecureStorage

# Configure logging
logger = logging.getLogger('schwab_api.oauth.token_manager')


class TokenManager:
    """
    Manages OAuth tokens securely.
    
    This class handles storage, retrieval, validation, and refresh of OAuth
    tokens for the Schwab API.
    """
    
    def __init__(self, secure_storage: SecureStorage, api_type: str, settings_manager: Any):
        """
        Initialize the token manager.
        
        Args:
            secure_storage (SecureStorage): Secure storage instance
            api_type (str): API type ('market_data' or 'accounts_trading')
            settings_manager (Any): Settings manager instance
        """
        self.secure_storage = secure_storage
        self.api_type = api_type
        self.settings = settings_manager
        
        # Token state
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = 0
        
        # Token storage key
        self.token_key = f"schwab_oauth_{api_type}_tokens"
        
        # Try to load existing tokens
        self._load_tokens()
    
    def save_tokens(self, access_token: str, refresh_token: str, expires_in: int) -> bool:
        """
        Save OAuth tokens securely.
        
        Args:
            access_token (str): OAuth access token
            refresh_token (str): OAuth refresh token
            expires_in (int): Token expiration time in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Update in-memory state
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = time.time() + expires_in
        
        # Prepare token data
        token_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expiry': self.token_expiry,
            'api_type': self.api_type,
            'created_at': time.time()
        }
        
        # Save to secure storage
        success = self.secure_storage.store(self.token_key, token_data)
        
        if success:
            logger.info(f"Saved {self.api_type} tokens (expires in {expires_in}s)")
        else:
            logger.error(f"Failed to save {self.api_type} tokens")
            
        return success
    
    def _load_tokens(self) -> bool:
        """
        Load OAuth tokens from secure storage.
        
        Returns:
            bool: True if tokens were loaded successfully, False otherwise
        """
        token_data = self.secure_storage.retrieve(self.token_key)
        
        if not token_data:
            logger.debug(f"No stored tokens found for {self.api_type}")
            return False
            
        # Validate token data
        required_fields = ['access_token', 'refresh_token', 'expiry', 'api_type']
        if not all(field in token_data for field in required_fields):
            logger.warning(f"Stored token data is missing required fields")
            return False
            
        # Ensure API type matches
        if token_data['api_type'] != self.api_type:
            logger.warning(f"Stored token API type mismatch: {token_data['api_type']} != {self.api_type}")
            return False
            
        # Update in-memory state
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.token_expiry = token_data['expiry']
        
        logger.debug(f"Loaded {self.api_type} tokens from secure storage")
        return True
    
    def is_token_valid(self, buffer_seconds: int = 60) -> bool:
        """
        Check if the current access token is valid.
        
        Args:
            buffer_seconds (int): Buffer time in seconds to require for token validity
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        # Check if we have a token
        if not self.access_token:
            return False
            
        # Check if the token is expired (with buffer)
        remaining = self.token_expiry - time.time()
        is_valid = remaining > buffer_seconds
        
        if not is_valid:
            logger.debug(f"Token expired or expiring soon (remaining: {int(remaining)}s)")
            
        return is_valid
    
    def refresh_access_token(self, client_id: str, client_secret: str, token_url: str) -> bool:
        """
        Refresh the access token using the refresh token.
        
        Args:
            client_id (str): OAuth client ID
            client_secret (str): OAuth client secret
            token_url (str): Token endpoint URL
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            TokenError: If refresh fails
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            raise TokenError("No refresh token available")
            
        logger.info("Refreshing access token")
        
        # Prepare the request
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        try:
            response = requests.post(
                token_url,
                headers=headers,
                data=data,
                timeout=self.settings.get('network', 'request_timeout_seconds', 30)
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Extract tokens
                access_token = token_data.get('access_token')
                refresh_token = token_data.get('refresh_token', self.refresh_token)  # Use existing if not provided
                expires_in = token_data.get('expires_in', 3600)
                
                # Save tokens
                self.save_tokens(access_token, refresh_token, expires_in)
                
                logger.info("Access token refreshed successfully")
                return True
            else:
                error_msg = f"Token refresh failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', '')}: {error_data.get('error_description', '')}"
                except:
                    error_msg += f" - {response.text}"
                    
                logger.error(error_msg)
                raise TokenError(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"Network error refreshing token: {str(e)}"
            logger.error(error_msg)
            raise TokenError(error_msg)
            
        except Exception as e:
            error_msg = f"Error refreshing token: {str(e)}"
            logger.error(error_msg)
            raise TokenError(error_msg)
    
    def get_auth_header(self) -> Dict[str, str]:
        """
        Get authorization header with the current access token.
        
        Returns:
            Dict[str, str]: Authorization header
            
        Raises:
            TokenError: If no valid token is available
        """
        if not self.access_token:
            raise TokenError("No access token available")
            
        return {'Authorization': f'Bearer {self.access_token}'}
    
    def clear_tokens(self) -> bool:
        """
        Clear all stored tokens.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Clear in-memory state
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = 0
        
        # Remove from secure storage
        return self.secure_storage.delete(self.token_key)
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get information about the current token.
        
        Returns:
            Dict[str, Any]: Token information
        """
        if not self.access_token:
            return {
                'status': 'no_token',
                'api_type': self.api_type
            }
            
        now = time.time()
        expires_in = self.token_expiry - now
        
        return {
            'status': 'valid' if expires_in > 0 else 'expired',
            'api_type': self.api_type,
            'expires_in': int(expires_in),
            'has_refresh_token': bool(self.refresh_token)
        }