#!/usr/bin/env python3
"""
Direct PostgreSQL Schema Update Script
:TechnologyVersion Python 3.10+, PostgreSQL 14+
:Context :DatabaseMigration for multi-timeframe data collection
"""

import sys
import psycopg2
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('apply_schema_changes')

def apply_schema_changes():
    """Apply PostgreSQL schema changes directly using psycopg2"""
    
    schema_changes = """
    -- Add timeframe and data_source columns to price_data table
    ALTER TABLE price_data 
    ADD COLUMN IF NOT EXISTS timeframe VARCHAR(20) NOT NULL DEFAULT '1day';

    ALTER TABLE price_data 
    ADD COLUMN IF NOT EXISTS data_source VARCHAR(50) NOT NULL DEFAULT 'yfinance';

    -- Drop the existing unique constraint if it exists
    ALTER TABLE price_data 
    DROP CONSTRAINT IF EXISTS unique_price_point;

    -- Add a new unique constraint that includes timeframe and data_source
    ALTER TABLE price_data 
    ADD CONSTRAINT unique_price_point 
        UNIQUE (symbol_id, timestamp, timeframe, data_source);

    -- Add index for efficient querying by timeframe
    DROP INDEX IF EXISTS idx_price_data_timeframe;
    CREATE INDEX idx_price_data_timeframe 
        ON price_data USING btree (timeframe);

    -- Add index for efficient querying by data source
    DROP INDEX IF EXISTS idx_price_data_data_source;
    CREATE INDEX idx_price_data_data_source 
        ON price_data USING btree (data_source);

    -- Add composite index for common query patterns
    DROP INDEX IF EXISTS idx_price_data_symbol_timeframe_time;
    CREATE INDEX idx_price_data_symbol_timeframe_time 
        ON price_data USING btree (symbol_id, timeframe, timestamp);

    -- Add comments for documentation
    COMMENT ON COLUMN price_data.timeframe IS 'Time interval of price data (e.g., 1min, 5min, 15min, 30min, 60min, 1day)';
    COMMENT ON COLUMN price_data.data_source IS 'Source of price data (e.g., yfinance, alphavantage, internal)';
    """
    
    try:
        logger.info("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(
            host="localhost",
            database="market_data_system",
            user="postgres",
            password="postgres"  # Assuming default password, change if needed
        )
        
        # Set autocommit to true for DDL operations
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            logger.info("Applying schema changes...")
            cursor.execute(schema_changes)
            
        logger.info("Schema changes applied successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error applying schema changes: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()

def main():
    """Main entry point"""
    print("\n=== PostgreSQL Schema Update ===\n")
    
    success = apply_schema_changes()
    
    if success:
        print("\n✅ Schema changes applied successfully!")
        sys.exit(0)
    else:
        print("\n❌ Failed to apply schema changes")
        sys.exit(1)

if __name__ == "__main__":
    main()