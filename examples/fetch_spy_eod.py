#!/usr/bin/env python
"""
Fetch SPY EOD (End of Day) Data
:TechnologyVersion Python 3.10+
:AuthenticationPattern OAuth2
:DataFetchPattern MarketData

This script demonstrates how to authenticate with the Schwab API using OAuth
and fetch the End of Day (EOD) data for SPY from the previous Friday.
It uses the SchwabOAuthIntegration module for authentication and
MarketDataClient for retrieving the price history.
"""

import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path to import schwab_api
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import Schwab API modules
from schwab_api.auth.oauth_integration import SchwabOAuthIntegration
from schwab_api.market_data.market_data_client import MarketDataClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fetch_spy_eod')


def get_previous_friday() -> str:
    """
    Calculate the date of the previous Friday.
    
    Returns:
        str: Date string in format YYYY-MM-DD
    """
    today = datetime.date.today()
    days_since_friday = (today.weekday() - 4) % 7
    
    # If today is Friday, we want last Friday, not today
    if days_since_friday == 0:
        days_since_friday = 7
        
    previous_friday = today - datetime.timedelta(days=days_since_friday)
    return previous_friday.strftime('%Y-%m-%d')


def fetch_spy_eod_data(client: MarketDataClient, date: str) -> Optional[Dict[str, Any]]:
    """
    Fetch SPY EOD data for the specified date
    
    Args:
        client: MarketDataClient instance
        date: Date string in format YYYY-MM-DD
    
    Returns:
        Dictionary of price history data or None if failed
    """
    try:
        logger.info(f"Fetching SPY EOD data for {date}")
        
        # Fetch price history for SPY
        price_history = client.get_price_history(
            symbol="SPY",
            start_date=date,
            end_date=date,
            frequency="daily"
        )
        
        return price_history
    except Exception as e:
        logger.error(f"Error fetching SPY EOD data: {str(e)}")
        return None


def display_price_data(price_data: Dict[str, Any]) -> None:
    """
    Format and display the price data
    
    Args:
        price_data: Dictionary containing price history data
    """
    if not price_data or 'candles' not in price_data or not price_data['candles']:
        logger.error("No price data available")
        print("No price data available for SPY on the specified date.")
        return
    
    # Get the first (and only) candle
    candle = price_data['candles'][0]
    
    # Format date
    date_time = datetime.datetime.fromtimestamp(candle['datetime'] / 1000)
    formatted_date = date_time.strftime('%Y-%m-%d')
    
    # Display results
    print("\n====== SPY EOD Data ======")
    print(f"Date: {formatted_date}")
    print(f"Open: ${candle['open']:.2f}")
    print(f"High: ${candle['high']:.2f}")
    print(f"Low: ${candle['low']:.2f}")
    print(f"Close: ${candle['close']:.2f}")
    print(f"Volume: {candle['volume']:,}")
    
    # Calculate day's change
    change = candle['close'] - candle['open']
    change_percent = (change / candle['open']) * 100
    change_sign = "+" if change >= 0 else ""
    print(f"Day's Change: {change_sign}${change:.2f} ({change_sign}{change_percent:.2f}%)")
    print("==========================\n")


def main():
    """Main function"""
    logger.info("Starting SPY EOD data fetch")
    
    try:
        # Get previous Friday's date
        previous_friday = get_previous_friday()
        logger.info(f"Previous Friday's date: {previous_friday}")
        
        # Create OAuth integration using default configuration
        logger.info("Initializing Schwab API OAuth integration")
        oauth_integration = SchwabOAuthIntegration.create_default_instance(api_type="market_data")
        
        # Create API client
        oauth_client = oauth_integration.get_oauth_client()
        
        # Authenticate
        logger.info("Authenticating with Schwab API")
        if not oauth_client.authenticate():
            logger.error("Authentication failed")
            print("Authentication failed. Please check your credentials.")
            return
        
        logger.info("Authentication successful")
        
        # Create market data client
        market_data_client = MarketDataClient(oauth_client)
        
        # Fetch SPY EOD data
        spy_data = fetch_spy_eod_data(market_data_client, previous_friday)
        
        if spy_data:
            # Display the results
            display_price_data(spy_data)
            
            # Optionally, save the data to a file
            with open(f"spy_eod_{previous_friday}.json", "w") as f:
                json.dump(spy_data, f, indent=2)
                logger.info(f"Data saved to spy_eod_{previous_friday}.json")
        else:
            print("Failed to fetch SPY EOD data.")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Error: {str(e)}")
    
    logger.info("SPY EOD data fetch completed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\nProcess interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        print(f"\nError: {str(e)}")