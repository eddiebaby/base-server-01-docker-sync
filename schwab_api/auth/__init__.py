"""
Authentication module for Schwab API

This module provides authentication mechanisms for the Schwab API,
including OAuth authentication.
"""

from .auth_manager import AuthenticationManager
from .exceptions import AuthenticationError

# Import specific OAuth components
from .oauth.oauth_client import OAuthClient

__all__ = [
    'AuthenticationManager',
    'OAuthClient',
    'AuthenticationError'
]