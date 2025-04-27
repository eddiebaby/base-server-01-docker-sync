"""
Market Data Client for Schwab API

This module provides specialized access to market data endpoints of the Schwab API.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import date, datetime, timedelta

# Configure logging
logger = logging.getLogger('schwab_api.market_data')


class MarketDataClient:
    """
    Client for accessing market data from the Schwab API.
    
    This class provides specialized methods for retrieving market data,
    including quotes, historical prices, and other market information.
    """
    
    def __init__(self, api_client):
        """
        Initialize the market data client.
        
        Args:
            api_client: The main Schwab API client
        """
        self.api = api_client
        logger.info("Initialized Market Data client")
    
    def get_quotes(
        self,
        symbols: Union[str, List[str]],
        fields: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get quotes for the specified symbols.
        
        Args:
            symbols (Union[str, List[str]]): Symbol or list of symbols
            fields (Optional[str]): Comma-separated list of fields to return
            
        Returns:
            Dict[str, Any]: Quote data keyed by symbol
        """
        # Delegate to the core API
        return self.api.get_quotes(symbols, fields)
    
    def get_price_history(
        self,
        symbol: str,
        period_type: str = 'day',
        period: int = 10,
        frequency_type: str = 'minute',
        frequency: int = 5
    ) -> Dict[str, Any]:
        """
        Get price history for a symbol.
        
        Args:
            symbol (str): Symbol to get history for
            period_type (str): Type of period (day, month, year, etc.)
            period (int): Number of periods
            frequency_type (str): Type of frequency (minute, hour, day, etc.)
            frequency (int): Frequency value
            
        Returns:
            Dict[str, Any]: Price history data
        """
        params = {
            'symbol': symbol,
            'periodType': period_type,
            'period': period,
            'frequencyType': frequency_type,
            'frequency': frequency
        }
        
        return self.api.get('priceHistory', params=params)
    
    def get_option_chain(
        self,
        symbol: str,
        strike_count: int = 10,
        include_quotes: bool = True,
        strategy: str = 'SINGLE'
    ) -> Dict[str, Any]:
        """
        Get option chain for a symbol.
        
        Args:
            symbol (str): Symbol to get options for
            strike_count (int): Number of strikes to return
            include_quotes (bool): Whether to include quotes
            strategy (str): Option strategy
            
        Returns:
            Dict[str, Any]: Option chain data
        """
        params = {
            'symbol': symbol,
            'strikeCount': strike_count,
            'includeQuotes': str(include_quotes).lower(),
            'strategy': strategy
        }
        
        return self.api.get('optionChain', params=params)
    
    def get_market_hours(
        self,
        markets: Union[str, List[str]],
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get market hours for specified markets.
        
        Args:
            markets (Union[str, List[str]]): Market or list of markets
            date_str (Optional[str]): Date in format 'YYYY-MM-DD'
            
        Returns:
            Dict[str, Any]: Market hours data
        """
        # Convert list to comma-separated string
        if isinstance(markets, list):
            markets_str = ','.join(markets)
        else:
            markets_str = markets
            
        params = {'markets': markets_str}
        
        # Add date if provided
        if date_str:
            params['date'] = date_str
        
        return self.api.get('marketHours', params=params)
    
    def search_instruments(
        self,
        symbol: str,
        projection: str = 'symbol-search'
    ) -> Dict[str, Any]:
        """
        Search for instruments by symbol or description.
        
        Args:
            symbol (str): Symbol or keywords to search for
            projection (str): Type of search
            
        Returns:
            Dict[str, Any]: Search results
        """
        params = {
            'symbol': symbol,
            'projection': projection
        }
        
        return self.api.get('instruments', params=params)
    
    def get_movers(
        self,
        index: str = 'SPX',
        direction: str = 'up',
        change: str = 'percent'
    ) -> Dict[str, Any]:
        """
        Get market movers for a specified index.
        
        Args:
            index (str): Index to get movers for
            direction (str): Direction ('up' or 'down')
            change (str): Change type ('percent' or 'value')
            
        Returns:
            Dict[str, Any]: Market movers data
        """
        params = {
            'index': index,
            'direction': direction,
            'change': change
        }
        
        return self.api.get('movers', params=params)
    
    def get_market_data(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a generic market data request.
        
        Args:
            endpoint (str): API endpoint
            params (Optional[Dict[str, Any]]): Query parameters
            
        Returns:
            Dict[str, Any]: API response
        """
        return self.api.get(endpoint, params=params)
    
    def format_quotes(self, quotes_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format quotes data into a more usable structure.
        
        Args:
            quotes_data (Dict[str, Any]): Raw quotes data from the API
            
        Returns:
            List[Dict[str, Any]]: List of formatted quote objects
        """
        formatted_quotes = []
        
        # Handle both array and object formats
        if isinstance(quotes_data, dict):
            for symbol, quote in quotes_data.items():
                # Ensure symbol is included
                if 'symbol' not in quote:
                    quote['symbol'] = symbol
                formatted_quotes.append(quote)
        elif isinstance(quotes_data, list):
            formatted_quotes = quotes_data
        
        return formatted_quotes