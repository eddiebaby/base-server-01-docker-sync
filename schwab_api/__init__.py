"""
Schwab API Client - Modular implementation with OAuth authentication

This package provides a modular interface to the Charles Schwab API
with support for OAuth authentication, market data, and trading operations.
"""

__version__ = '0.1.0'

from .core import SchwabAPI

__all__ = ['SchwabAPI']