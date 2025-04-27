-- SQL Script to modify the price_data table for multi-timeframe and multi-source support
-- :TechnologyVersion PostgreSQL 14+
-- :Context :DataPipeline for market data collection from multiple sources

-- Add timeframe and data_source columns to price_data table
ALTER TABLE price_data
ADD COLUMN timeframe VARCHAR(20) NOT NULL DEFAULT '1day';

ALTER TABLE price_data
ADD COLUMN data_source VARCHAR(50) NOT NULL DEFAULT 'yfinance';

-- Drop the existing unique constraint if it exists
ALTER TABLE price_data
DROP CONSTRAINT IF EXISTS unique_price_point;

-- Add a new unique constraint that includes timeframe and data_source
ALTER TABLE price_data
ADD CONSTRAINT unique_price_point
    UNIQUE (symbol_id, timestamp, timeframe, data_source);

-- Add index for efficient querying by timeframe
CREATE INDEX idx_price_data_timeframe
    ON price_data USING btree (timeframe);

-- Add index for efficient querying by data source
CREATE INDEX idx_price_data_data_source
    ON price_data USING btree (data_source);

-- Add composite index for common query patterns
CREATE INDEX idx_price_data_symbol_timeframe_time
    ON price_data USING btree (symbol_id, timeframe, timestamp);

-- Add comments for documentation (PostgreSQL way)
COMMENT ON COLUMN price_data.timeframe IS 'Time interval of price data (e.g., 1min, 5min, 15min, 30min, 60min, 1day)';
COMMENT ON COLUMN price_data.data_source IS 'Source of price data (e.g., yfinance, alphavantage, internal)';