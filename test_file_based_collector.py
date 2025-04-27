#!/usr/bin/env python3
"""
Test Script for File-Based Multi-Timeframe Market Data Collector
:TechnologyVersion Python 3.10+
:Context :Test for database-free multi-timeframe data collection

This script tests the file-based collector that stores data in CSV files
instead of requiring a PostgreSQL database.
"""

import os
import sys
import logging
import datetime
from pathlib import Path

# Add parent directory to path for importing project modules
sys.path.append(str(Path(__file__).resolve().parent))
from data_collection.file_based_multi_timeframe_collector import FileBasedMultiTimeframeCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('test_file_based_collector')

def test_single_symbol_collection():
    """
    Test collecting data for S&P 500 at daily and hourly timeframes.
    Stores results in CSV files under the market_data directory.
    """
    logger.info("Testing file-based data collection for ^GSPC at daily and hourly timeframes")
    
    try:
        # Initialize collector
        collector = FileBasedMultiTimeframeCollector()
        
        # Set test parameters - just one week of data
        symbol = "^GSPC"
        timeframes = ["1day", "60min"]
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Collect multi-timeframe data
        results = collector.collect_multi_timeframe_data(
            symbols=[symbol],
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date
        )
        
        # Print collection summary
        print("\n=== Collection Results ===")
        print(f"Symbols Processed: {results['symbols_processed']}")
        print(f"Symbols Failed: {results['symbols_failed']}")
        print(f"Total Rows Collected: {results['total_rows_collected']}")
        print(f"Total Rows Stored: {results['total_rows_stored']}")
        print(f"Success Rate: {results['success_rate']}%")
        
        # Print timeframe statistics
        print("\n=== Timeframe Statistics ===")
        for timeframe, stats in results['timeframe_stats'].items():
            print(f"{timeframe}:")
            print(f"  Symbols Processed: {stats['symbols_processed']}")
            print(f"  Rows Collected: {stats['rows_collected']}")
            print(f"  Rows Stored: {stats['rows_stored']}")
        
        # Verify files were created
        success = True
        for timeframe in timeframes:
            data_file = os.path.join(collector.data_dir, symbol.replace('^', ''), f"{timeframe}.csv")
            if os.path.exists(data_file):
                file_size = os.path.getsize(data_file)
                print(f"\nFile created: {data_file} ({file_size} bytes)")
            else:
                print(f"\nERROR: File not created: {data_file}")
                success = False
                
        return success
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

def main():
    """Run verification tests for file-based collector."""
    print("\n=== File-Based Multi-Timeframe Market Data Collector Test ===\n")
    
    # Test data collection
    collection_ok = test_single_symbol_collection()
    
    # Print overall results
    print("\n=== Test Results ===")
    if collection_ok:
        print("✅ All tests passed! The file-based multi-timeframe collector is working correctly.")
        print("\nYou can now run collect_file_based_data.bat to collect data for all symbols and timeframes.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()