#!/usr/bin/env python3
"""
CLI Script for Market Data Collection
:TechnologyVersion Python 3.10+
:ArchitecturalPattern :CommandLineInterface

This script provides a command-line interface for collecting market data
using the MarketDataCollector module. It accepts symbols and date ranges
as parameters and stores the collected data in the database.
"""

import os
import sys
import argparse
import logging
import datetime
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for importing project modules
sys.path.append(str(Path(__file__).parent.parent))
from data_collection.market_data_collector import MarketDataCollector, MarketDataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('collect_market_data')

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Collect market data (OHLCV) for specified symbols and date range'
    )
    
    # Symbol arguments
    symbol_group = parser.add_mutually_exclusive_group(required=True)
    symbol_group.add_argument(
        '-s', '--symbol', 
        help='Single stock symbol to collect data for (e.g., AAPL)'
    )
    symbol_group.add_argument(
        '-f', '--file', 
        help='File containing list of symbols, one per line'
    )
    symbol_group.add_argument(
        '-l', '--list', 
        help='Comma-separated list of symbols (e.g., AAPL,MSFT,GOOG)'
    )
    
    # Date range arguments
    parser.add_argument(
        '--start-date', 
        required=True,
        help='Start date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--end-date', 
        default=None,
        help='End date in YYYY-MM-DD format (default: today)'
    )
    
    # Additional options
    parser.add_argument(
        '--interval', 
        default='1d',
        choices=['1d', '1wk', '1mo', '1h', '1m'],
        help='Data interval (default: 1d)'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()

def validate_date(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD)."""
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def get_symbols(args) -> List[str]:
    """Get list of symbols from arguments."""
    if args.symbol:
        return [args.symbol.upper()]
    elif args.list:
        return [s.strip().upper() for s in args.list.split(',')]
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                return [line.strip().upper() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Error reading symbols file: {e}")
            sys.exit(1)
    return []

def main():
    """Main entry point for the script."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose output enabled")
    
    # Validate dates
    if not validate_date(args.start_date):
        logger.error(f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD.")
        sys.exit(1)
    
    if args.end_date and not validate_date(args.end_date):
        logger.error(f"Invalid end date format: {args.end_date}. Use YYYY-MM-DD.")
        sys.exit(1)
    
    # Get symbols
    symbols = get_symbols(args)
    if not symbols:
        logger.error("No symbols specified")
        sys.exit(1)
    
    logger.info(f"Collecting market data for {len(symbols)} symbols " +
                f"from {args.start_date} to {args.end_date or 'today'} " +
                f"with interval {args.interval}")
    
    # Initialize market data collector
    collector = MarketDataCollector()
    
    try:
        # Collect market data
        results = collector.collect_market_data(
            symbols=symbols,
            start_date=args.start_date,
            end_date=args.end_date,
            interval=args.interval
        )
        
        # Print results summary
        print("\n=== Market Data Collection Results ===")
        print(f"Symbols Processed: {results['symbols_processed']}")
        print(f"Symbols Failed: {results['symbols_failed']}")
        print(f"Total Rows Collected: {results['total_rows_collected']}")
        print(f"Total Rows Stored: {results['total_rows_stored']}")
        print(f"Success Rate: {results['success_rate']}%")
        print(f"Started At: {results['started_at']}")
        print(f"Completed At: {results['completed_at']}")
        
        # Print errors if any
        if results['errors']:
            print("\n=== Errors ===")
            for error in results['errors']:
                print(f"{error['symbol']}: {error['error']}")
        
        # Exit with appropriate code
        if results['symbols_failed'] > 0 and results['symbols_processed'] == 0:
            logger.error("All symbols failed")
            sys.exit(2)
        elif results['symbols_failed'] > 0:
            logger.warning("Some symbols failed")
            sys.exit(0)  # Still a partial success
        else:
            logger.info("All symbols processed successfully")
            sys.exit(0)
            
    except MarketDataError as e:
        logger.error(f"Market data collection error: {e}")
        sys.exit(3)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(4)

if __name__ == "__main__":
    main()