#!/usr/bin/env python3
"""
Test Script for Multi-Timeframe Market Data Collector
:TechnologyVersion Python 3.10+
:Context :Test for multi-timeframe data collection

This script performs basic verification tests to ensure that:
1. Database schema changes were applied correctly
2. Multi-timeframe collector can fetch and store data correctly
"""

import os
import sys
import logging
from pathlib import Path
import datetime

# Add parent directory to path for importing project modules
sys.path.append(str(Path(__file__).resolve().parent))
from data_collection.multi_timeframe_collector import MultiTimeframeMarketDataCollector
from db.connection_manager import ConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('test_multi_timeframe_collector')

def verify_schema_changes():
    """Verify that the database schema includes the new columns."""
    try:
        conn_manager = ConnectionManager()
        
        # Check if timeframe and data_source columns exist in price_data table
        query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='price_data' 
        AND column_name IN ('timeframe', 'data_source')
        """
        results = conn_manager.execute_query(query)
        
        if len(results) == 2:
            logger.info("✅ Schema validation: timeframe and data_source columns exist")
            return True
        else:
            found_columns = [row[0] for row in results]
            missing_columns = set(['timeframe', 'data_source']) - set(found_columns)
            logger.error(f"❌ Schema validation failed: Missing columns: {missing_columns}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Schema validation error: {e}")
        return False

def test_single_symbol_collection():
    """Test collecting data for S&P 500 at daily timeframe."""
    logger.info("Testing data collection for ^GSPC at daily timeframe")
    
    try:
        # Initialize collector
        collector = MultiTimeframeMarketDataCollector()
        
        # Set test parameters - just one week of daily data
        symbol = "^GSPC"
        timeframe = "1day"
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Test fetching data
        data = collector.fetch_ohlcv_data_multi_timeframe(symbol, timeframe, start_date, end_date)
        if data.empty:
            logger.error(f"❌ No data fetched for {symbol}")
            return False
            
        logger.info(f"✅ Successfully fetched {len(data)} rows for {symbol}")
        
        # Validate data
        validated_data = collector.validate_data_multi_timeframe(data)
        logger.info(f"✅ Data validation successful, {len(validated_data)} valid rows")
        
        # Store data
        rows_stored = collector.store_ohlcv_data_multi_timeframe(validated_data)
        logger.info(f"✅ Successfully stored {rows_stored} rows for {symbol}")
        
        # Verify data was stored with correct timeframe
        conn_manager = ConnectionManager()
        query = """
        SELECT COUNT(*) FROM price_data p
        JOIN market_symbols ms ON p.symbol_id = ms.id
        WHERE ms.symbol = %s AND p.timeframe = %s
        AND p.timestamp >= %s AND p.timestamp <= %s
        """
        results = conn_manager.execute_query(
            query, 
            (symbol, timeframe, start_date, end_date + " 23:59:59")
        )
        
        stored_count = results[0][0] if results else 0
        if stored_count > 0:
            logger.info(f"✅ Verified {stored_count} rows in database with correct timeframe")
            return True
        else:
            logger.error("❌ No data found in database with correct timeframe")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

def main():
    """Run verification tests."""
    print("\n=== Multi-Timeframe Market Data Collector Test ===\n")
    
    # Step 1: Verify schema changes
    print("Step 1: Verifying database schema changes...")
    schema_ok = verify_schema_changes()
    
    if not schema_ok:
        print("\n❌ Schema verification failed. Please run schema_updates_timeframe.sql first.")
        sys.exit(1)
    
    # Step 2: Test data collection
    print("\nStep 2: Testing data collection for a single symbol...")
    collection_ok = test_single_symbol_collection()
    
    # Print overall results
    print("\n=== Test Results ===")
    if schema_ok and collection_ok:
        print("✅ All tests passed! The multi-timeframe collector is working correctly.")
        print("\nYou can now run collect_multi_timeframe_data.bat to collect data for all symbols and timeframes.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()