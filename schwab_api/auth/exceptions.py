"""
Authentication-related exceptions for Schwab API

This module defines custom exceptions for authentication-related errors.
"""

class AuthenticationError(Exception):
    """Base class for all authentication-related errors"""
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


class TokenError(AuthenticationError):
    """Error related to OAuth token operations"""
    pass


class CallbackError(AuthenticationError):
    """Error related to OAuth callback operations"""
    pass


class ConfigurationError(AuthenticationError):
    """Error related to authentication configuration"""
    pass


class NetworkError(AuthenticationError):
    """Network-related authentication error"""
    pass