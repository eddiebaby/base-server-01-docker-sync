"""
Authentication Manager for Schwab API

This module defines the abstract interface for authentication mechanisms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class AuthenticationManager(ABC):
    """
    Abstract base class for all authentication mechanisms.
    
    This defines the interface that all authentication implementations
    must provide to be usable with the Schwab API.
    """
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Initiate the authentication flow.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        pass
        
    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if current authentication is valid.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        pass
        
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dict[str, str]: Headers to include in API requests
        """
        pass
        
    @abstractmethod
    def refresh_auth(self) -> bool:
        """
        Refresh authentication credentials.
        
        Returns:
            bool: True if refresh was successful, False otherwise
        """
        pass

    @property
    @abstractmethod
    def api_type(self) -> str:
        """
        Get the API type this authentication is for.
        
        Returns:
            str: API type (e.g., 'market_data', 'accounts_trading')
        """
        pass
        
    @property
    @abstractmethod
    def auth_method(self) -> str:
        """
        Get the authentication method name.
        
        Returns:
            str: Authentication method name (e.g., 'oauth', 'api_key')
        """
        pass