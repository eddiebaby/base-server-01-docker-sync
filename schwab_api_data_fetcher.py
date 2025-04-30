#!/usr/bin/env python
"""
Schwab API Data Fetcher
:TechnologyVersion Python 3.10+
:AuthenticationPattern OAuth2
:DataFetchPattern MarketData
:SecurityPattern SecureCredentialManagement

This script authenticates with the Schwab API using OAuth 2.0 and fetches
market data for specified symbols. It demonstrates proper authentication,
error handling, and data formatting using the established OAuth infrastructure.

Usage:
    python schwab_api_data_fetcher.py --symbols AAPL,MSFT,GOOGL
    python schwab_api_data_fetcher.py --symbols SPY --data-type price-history
    python schwab_api_data_fetcher.py --symbols AAPL,MSFT --output json
"""

import sys
import json
import logging
import argparse
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('schwab_api_data_fetcher')

# Import Schwab API modules
from schwab_api.auth.oauth_integration import SchwabOAuthIntegration
from schwab_api.market_data.market_data_client import MarketDataClient


def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Set up command line argument parser
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Fetch market data from Schwab API',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--symbols', 
        type=str, 
        default='AAPL,MSFT,GOOGL',
        help='Comma-separated list of symbols to fetch data for'
    )
    
    parser.add_argument(
        '--data-type', 
        type=str, 
        choices=['quotes', 'price-history', 'option-chain', 'movers'],
        default='quotes',
        help='Type of market data to fetch'
    )
    
    parser.add_argument(
        '--period', 
        type=int, 
        default=10,
        help='Period for price history (number of days/months/years)'
    )
    
    parser.add_argument(
        '--period-type', 
        type=str, 
        choices=['day', 'month', 'year', 'ytd'],
        default='day',
        help='Period type for price history'
    )
    
    parser.add_argument(
        '--frequency-type', 
        type=str, 
        choices=['minute', 'daily', 'weekly', 'monthly'],
        default='daily',
        help='Frequency type for price history'
    )
    
    parser.add_argument(
        '--frequency', 
        type=int, 
        default=1,
        help='Frequency for price history'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        choices=['table', 'json'],
        default='table',
        help='Output format'
    )
    
    parser.add_argument(
        '--save', 
        action='store_true',
        help='Save data to file'
    )
    
    return parser


def authenticate_with_schwab_api() -> Optional[MarketDataClient]:
    """
    Authenticate with Schwab API and create a market data client
    
    Returns:
        Optional[MarketDataClient]: Market data client if authentication successful, None otherwise
    """
    try:
        logger.info("Initializing Schwab API OAuth integration")
        
        # Create OAuth integration using default configuration
        oauth_integration = SchwabOAuthIntegration.create_default_instance(api_type="market_data")
        
        # Get OAuth client
        oauth_client = oauth_integration.get_oauth_client()
        
        # Authenticate
        logger.info("Authenticating with Schwab API")
        if not oauth_integration.authenticate():
            logger.error("Authentication failed")
            print("Authentication failed. Please check your credentials.")
            return None
        
        logger.info("Authentication successful")
        
        # Check token info
        token_info = oauth_integration.get_token_info()
        logger.info(f"Token expires in: {token_info.get('expires_in', 'unknown')} seconds")
        
        # Create market data client
        market_data_client = MarketDataClient(oauth_client)
        return market_data_client
        
    except Exception as e:
        logger.error(f"Error during authentication: {str(e)}")
        print(f"Authentication error: {str(e)}")
        return None


def fetch_quotes(client: MarketDataClient, symbols: List[str]) -> Optional[Dict[str, Any]]:
    """
    Fetch quotes for the specified symbols
    
    Args:
        client: MarketDataClient instance
        symbols: List of symbols to fetch quotes for
    
    Returns:
        Optional[Dict[str, Any]]: Quote data or None if failed
    """
    try:
        logger.info(f"Fetching quotes for {symbols}")
        quotes = client.get_quotes(symbols)
        return quotes
    except Exception as e:
        logger.error(f"Error fetching quotes: {str(e)}")
        return None


def fetch_price_history(
    client: MarketDataClient, 
    symbol: str,
    period_type: str = 'day',
    period: int = 10,
    frequency_type: str = 'daily',
    frequency: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Fetch price history for the specified symbol
    
    Args:
        client: MarketDataClient instance
        symbol: Symbol to fetch price history for
        period_type: Type of period (day, month, year, ytd)
        period: Number of periods
        frequency_type: Type of frequency (minute, daily, weekly, monthly)
        frequency: Frequency value
    
    Returns:
        Optional[Dict[str, Any]]: Price history data or None if failed
    """
    try:
        logger.info(f"Fetching price history for {symbol}")
        
        # Map frequency_type to the API's expected frequencyType
        frequency_type_map = {
            'minute': 'minute',
            'daily': 'day',
            'weekly': 'week',
            'monthly': 'month'
        }
        
        api_frequency_type = frequency_type_map.get(frequency_type, 'day')
        
        price_history = client.get_price_history(
            symbol=symbol,
            period_type=period_type,
            period=period,
            frequency_type=api_frequency_type,
            frequency=frequency
        )
        
        return price_history
    except Exception as e:
        logger.error(f"Error fetching price history: {str(e)}")
        return None


def fetch_option_chain(client: MarketDataClient, symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch option chain for the specified symbol
    
    Args:
        client: MarketDataClient instance
        symbol: Symbol to fetch option chain for
    
    Returns:
        Optional[Dict[str, Any]]: Option chain data or None if failed
    """
    try:
        logger.info(f"Fetching option chain for {symbol}")
        option_chain = client.get_option_chain(symbol)
        return option_chain
    except Exception as e:
        logger.error(f"Error fetching option chain: {str(e)}")
        return None


def fetch_movers(client: MarketDataClient, index: str = 'SPX') -> Optional[Dict[str, Any]]:
    """
    Fetch market movers for the specified index
    
    Args:
        client: MarketDataClient instance
        index: Index to fetch movers for
    
    Returns:
        Optional[Dict[str, Any]]: Market movers data or None if failed
    """
    try:
        logger.info(f"Fetching market movers for {index}")
        movers = client.get_movers(index=index)
        return movers
    except Exception as e:
        logger.error(f"Error fetching market movers: {str(e)}")
        return None


def display_quotes(quotes_data: Dict[str, Any], output_format: str = 'table') -> None:
    """
    Display quotes data in the specified format
    
    Args:
        quotes_data: Quotes data
        output_format: Output format ('table' or 'json')
    """
    if not quotes_data:
        print("No quotes data available.")
        return
    
    if output_format == 'json':
        print(json.dumps(quotes_data, indent=2))
        return
    
    # Format as table
    print("\n====== Market Quotes ======")
    print(f"{'Symbol':<6} {'Description':<30} {'Last Price':<12} {'Change':<10} {'% Change':<10} {'Volume':<12}")
    print("-" * 80)
    
    for symbol, quote in quotes_data.items():
        description = quote.get('description', '')[:30]
        last_price = quote.get('lastPrice', 0)
        change = quote.get('change', 0)
        percent_change = quote.get('percentChange', 0)
        volume = quote.get('volume', 0)
        
        change_sign = "+" if change >= 0 else ""
        
        print(f"{symbol:<6} {description:<30} ${last_price:<10.2f} {change_sign}{change:<8.2f} {change_sign}{percent_change:<8.2f}% {volume:<12,}")
    
    print("=" * 80)


def display_price_history(price_data: Dict[str, Any], symbol: str, output_format: str = 'table') -> None:
    """
    Display price history data in the specified format
    
    Args:
        price_data: Price history data
        symbol: Symbol the data is for
        output_format: Output format ('table' or 'json')
    """
    if not price_data or 'candles' not in price_data or not price_data['candles']:
        print("No price history data available.")
        return
    
    if output_format == 'json':
        print(json.dumps(price_data, indent=2))
        return
    
    # Format as table
    print(f"\n====== Price History for {symbol} ======")
    print(f"{'Date':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<12}")
    print("-" * 70)
    
    for candle in price_data['candles']:
        date_time = datetime.datetime.fromtimestamp(candle['datetime'] / 1000)
        formatted_date = date_time.strftime('%Y-%m-%d')
        
        print(f"{formatted_date:<12} ${candle['open']:<8.2f} ${candle['high']:<8.2f} ${candle['low']:<8.2f} ${candle['close']:<8.2f} {candle['volume']:<12,}")
    
    print("=" * 70)


def save_data_to_file(data: Dict[str, Any], filename: str) -> bool:
    """
    Save data to a JSON file
    
    Args:
        data: Data to save
        filename: Filename to save to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Data saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to file: {str(e)}")
        return False


def main():
    """Main function"""
    # Parse command line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    logger.info(f"Starting Schwab API data fetcher for symbols: {symbols}")
    
    # Authenticate and get market data client
    market_data_client = authenticate_with_schwab_api()
    if not market_data_client:
        return
    
    # Fetch data based on data type
    data = None
    if args.data_type == 'quotes':
        data = fetch_quotes(market_data_client, symbols)
        if data:
            display_quotes(data, args.output)
    
    elif args.data_type == 'price-history':
        # For price history, we fetch each symbol individually
        for symbol in symbols:
            symbol_data = fetch_price_history(
                market_data_client, 
                symbol,
                args.period_type,
                args.period,
                args.frequency_type,
                args.frequency
            )
            
            if symbol_data:
                display_price_history(symbol_data, symbol, args.output)
                
                # Save data if requested
                if args.save:
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{symbol}_{args.data_type}_{timestamp}.json"
                    save_data_to_file(symbol_data, filename)
    
    elif args.data_type == 'option-chain':
        # For option chain, we fetch each symbol individually
        for symbol in symbols:
            symbol_data = fetch_option_chain(market_data_client, symbol)
            
            if symbol_data and args.output == 'json':
                print(json.dumps(symbol_data, indent=2))
            elif symbol_data:
                print(f"\nOption chain data for {symbol} is too complex for table format.")
                print("Use --output json to see the full data.")
                
                # Save data if requested
                if args.save:
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{symbol}_{args.data_type}_{timestamp}.json"
                    save_data_to_file(symbol_data, filename)
    
    elif args.data_type == 'movers':
        # For movers, we use the first symbol as the index
        index = symbols[0] if symbols else 'SPX'
        movers_data = fetch_movers(market_data_client, index)
        
        if movers_data and args.output == 'json':
            print(json.dumps(movers_data, indent=2))
        elif movers_data:
            print(f"\n====== Market Movers for {index} ======")
            print(f"{'Symbol':<6} {'Description':<30} {'Last Price':<12} {'Change':<10} {'% Change':<10}")
            print("-" * 70)
            
            for mover in movers_data.get('movers', []):
                symbol = mover.get('symbol', '')
                description = mover.get('description', '')[:30]
                last_price = mover.get('lastPrice', 0)
                change = mover.get('change', 0)
                percent_change = mover.get('percentChange', 0)
                
                change_sign = "+" if change >= 0 else ""
                
                print(f"{symbol:<6} {description:<30} ${last_price:<10.2f} {change_sign}{change:<8.2f} {change_sign}{percent_change:<8.2f}%")
            
            print("=" * 70)
            
            # Save data if requested
            if args.save:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{index}_movers_{timestamp}.json"
                save_data_to_file(movers_data, filename)
    
    logger.info("Schwab API data fetcher completed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\nProcess interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        print(f"\nError: {str(e)}")