#!/usr/bin/env python3
"""
CLI Script for Multi-Timeframe Market Data Collection
:TechnologyVersion Python 3.10+
:ArchitecturalPattern :CommandLineInterface
:Context :DataCollection for market data across multiple timeframes

This script provides a command-line interface for collecting market data
at multiple timeframes using the MultiTimeframeMarketDataCollector.
It accepts symbols, timeframes, and date ranges as parameters and stores 
the collected data in the database with proper timeframe information.
"""

import os
import sys
import argparse
import logging
import datetime
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add parent directory to path for importing project modules
sys.path.append(str(Path(__file__).parent.parent))
from data_collection.multi_timeframe_collector import MultiTimeframeMarketDataCollector
from data_collection.market_data_collector import MarketDataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('collect_multi_timeframe_data')

# Create logs directory if needed
os.makedirs(os.path.join(os.path.dirname(__file__), '../logs'), exist_ok=True)
file_handler = logging.FileHandler(os.path.join(os.path.dirname(__file__), '../logs/multi_timeframe_data.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Collect market data (OHLCV) at multiple timeframes for specified symbols and date range'
    )
    
    # Symbol arguments
    symbol_group = parser.add_mutually_exclusive_group(required=True)
    symbol_group.add_argument(
        '-s', '--symbol', 
        help='Single stock symbol to collect data for (e.g., ^GSPC)'
    )
    symbol_group.add_argument(
        '-f', '--file', 
        help='File containing list of symbols, one per line'
    )
    symbol_group.add_argument(
        '-l', '--list', 
        help='Comma-separated list of symbols (e.g., ^GSPC,^VIX,^VXN)'
    )
    
    # Default symbols for quick collection
    symbol_group.add_argument(
        '--market-indices', 
        action='store_true',
        help='Collect data for market indices (^GSPC, ^VIX, ^VXN, ^SKEW, ^VVIX, ^TNX, ^NDX, ^RUT)'
    )
    symbol_group.add_argument(
        '--commodities', 
        action='store_true',
        help='Collect data for commodity futures (CL=F, GC=F, HG=F)'
    )
    symbol_group.add_argument(
        '--all', 
        action='store_true',
        help='Collect data for all default symbols (indices and commodities)'
    )
    
    # Timeframe arguments
    parser.add_argument(
        '-t', '--timeframes',
        default='1day',
        help='Comma-separated list of timeframes to collect (1min,5min,15min,30min,60min,1day)'
    )
    
    # Date range arguments
    parser.add_argument(
        '--start-date', 
        default=(datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d'),
        help='Start date in YYYY-MM-DD format (default: 1 year ago)'
    )
    parser.add_argument(
        '--end-date', 
        default=None,
        help='End date in YYYY-MM-DD format (default: today)'
    )
    
    # Additional options
    parser.add_argument(
        '--max-symbols', 
        type=int,
        default=None,
        help='Maximum number of symbols to process (useful for testing)'
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
    elif args.market_indices:
        return ['^GSPC', '^VIX', '^VXN', '^SKEW', '^VVIX', '^TNX', '^NDX', '^RUT']
    elif args.commodities:
        return ['CL=F', 'GC=F', 'HG=F']
    elif args.all:
        return ['^GSPC', '^VIX', '^VXN', '^SKEW', '^VVIX', '^TNX', '^NDX', '^RUT', 'CL=F', 'GC=F', 'HG=F']
    return []

def get_timeframes(args) -> List[str]:
    """Get list of timeframes from arguments."""
    if not args.timeframes:
        return ['1day']
    return [tf.strip() for tf in args.timeframes.split(',')]

def print_results_summary(results: Dict[str, Any]) -> None:
    """Print a summary of collection results."""
    print("\n=== Multi-Timeframe Market Data Collection Results ===")
    print(f"Symbols Processed: {results['symbols_processed']}")
    print(f"Symbols Failed: {results['symbols_failed']}")
    print(f"Total Rows Collected: {results['total_rows_collected']}")
    print(f"Total Rows Stored: {results['total_rows_stored']}")
    print(f"Success Rate: {results['success_rate']}%")
    print(f"Started At: {results['started_at']}")
    print(f"Completed At: {results['completed_at']}")
    
    # Print timeframe statistics
    print("\n=== Timeframe Statistics ===")
    for timeframe, stats in results['timeframe_stats'].items():
        print(f"{timeframe}:")
        print(f"  Symbols Processed: {stats['symbols_processed']}")
        print(f"  Rows Collected: {stats['rows_collected']}")
        print(f"  Rows Stored: {stats['rows_stored']}")
    
    # Print errors if any
    if results['errors']:
        print("\n=== Errors ===")
        # Group errors by timeframe
        timeframe_errors = {}
        for error in results['errors']:
            if error['timeframe'] not in timeframe_errors:
                timeframe_errors[error['timeframe']] = []
            timeframe_errors[error['timeframe']].append(error)
        
        for timeframe, errors in timeframe_errors.items():
            print(f"\n{timeframe} errors:")
            for error in errors[:5]:  # Show at most 5 errors per timeframe
                print(f"  {error['symbol']}: {error['error']}")
            
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")

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
    
    # Limit the number of symbols if requested
    if args.max_symbols and len(symbols) > args.max_symbols:
        logger.info(f"Limiting to {args.max_symbols} symbols out of {len(symbols)}")
        symbols = symbols[:args.max_symbols]
    
    # Get timeframes
    timeframes = get_timeframes(args)
    
    logger.info(f"Collecting market data for {len(symbols)} symbols " +
                f"at {len(timeframes)} timeframes " +
                f"from {args.start_date} to {args.end_date or 'today'}")
    
    # Initialize multi-timeframe market data collector
    collector = MultiTimeframeMarketDataCollector()
    
    try:
        # Collect multi-timeframe market data
        results = collector.collect_multi_timeframe_data(
            symbols=symbols,
            timeframes=timeframes,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        # Print results summary
        print_results_summary(results)
        
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