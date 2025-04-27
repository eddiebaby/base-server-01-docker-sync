-- PostgreSQL Database Schema for Market Data System
-- Target Version: PostgreSQL 14+
-- :ArchitecturalPattern :RelationalDatabase
-- :Context :DataPipeline for market data collection and analysis

-- Drop database if it exists (comment out in production)
-- DROP DATABASE IF EXISTS market_data_system;

-- Create database
CREATE DATABASE market_data_system
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Connect to the database
\c market_data_system

-- Enable PostGIS extension (if needed for geographical data)
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- Create tables
-- Market Symbols table: stores information about tradable market symbols
CREATE TABLE market_symbols (
    id SERIAL PRIMARY KEY,  -- Unique identifier
    symbol VARCHAR(20) NOT NULL,  -- Trading symbol (e.g., AAPL, MSFT)
    name VARCHAR(255) NOT NULL,  -- Full name of the security
    exchange VARCHAR(50) NOT NULL,  -- Exchange where symbol is traded
    sector VARCHAR(100),  -- Industry sector
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- :AuditTrail timestamp
    
    -- :DataIntegrityConstraint - Ensure symbols are unique
    CONSTRAINT unique_market_symbol UNIQUE (symbol),
    
    -- :DataIntegrityConstraint - Symbol format validation
    CONSTRAINT valid_symbol_format CHECK (symbol ~ '^[A-Z0-9\.\-]+$')
);

-- Add comment for documentation
COMMENT ON TABLE market_symbols IS 'Contains reference data for tradable market symbols used in the system';

-- Price Data table: stores historical price data for symbols
CREATE TABLE price_data (
    id BIGSERIAL PRIMARY KEY,  -- Unique identifier (BIGSERIAL for large datasets)
    symbol_id INTEGER NOT NULL,  -- Foreign key to market_symbols
    timestamp TIMESTAMPTZ NOT NULL,  -- When the price was recorded
    open NUMERIC(19,6) NOT NULL,  -- Opening price
    high NUMERIC(19,6) NOT NULL,  -- Highest price during the period
    low NUMERIC(19,6) NOT NULL,  -- Lowest price during the period
    close NUMERIC(19,6) NOT NULL,  -- Closing price
    volume BIGINT NOT NULL,  -- Trading volume
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- :AuditTrail timestamp
    
    -- :DataIntegrityConstraint - Link to market symbols
    CONSTRAINT fk_price_data_symbol 
        FOREIGN KEY (symbol_id) 
        REFERENCES market_symbols (id) 
        ON DELETE CASCADE,
        
    -- :DataIntegrityConstraint - Ensure data uniqueness by symbol and timestamp
    CONSTRAINT unique_price_point UNIQUE (symbol_id, timestamp),
    
    -- :DataIntegrityConstraint - Validate price and volume values
    CONSTRAINT positive_prices CHECK (
        open > 0 AND 
        high > 0 AND 
        low > 0 AND 
        close > 0
    ),
    CONSTRAINT valid_high_low CHECK (high >= low),
    CONSTRAINT non_negative_volume CHECK (volume >= 0)
);

-- Add comment for documentation
COMMENT ON TABLE price_data IS 'Historical price data (OHLCV) for market symbols';

-- Indicators table: stores calculated technical indicators
CREATE TABLE indicators (
    id BIGSERIAL PRIMARY KEY,  -- Unique identifier
    symbol_id INTEGER NOT NULL,  -- Foreign key to market_symbols
    indicator_type VARCHAR(50) NOT NULL,  -- Type of indicator (e.g., 'RSI', 'MACD')
    timestamp TIMESTAMPTZ NOT NULL,  -- When the indicator was calculated for
    value NUMERIC(19,6) NOT NULL,  -- Indicator value
    params JSONB,  -- Parameters used for calculation (flexible JSON format)
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- :AuditTrail timestamp
    
    -- :DataIntegrityConstraint - Link to market symbols
    CONSTRAINT fk_indicator_symbol 
        FOREIGN KEY (symbol_id) 
        REFERENCES market_symbols (id) 
        ON DELETE CASCADE,
        
    -- :DataIntegrityConstraint - Ensure indicator uniqueness
    CONSTRAINT unique_indicator_value UNIQUE (symbol_id, indicator_type, timestamp, (params::text))
);

-- Add comment for documentation
COMMENT ON TABLE indicators IS 'Technical indicators calculated from price data';

-- :PerformanceOptimization - Create indexes for common query patterns

-- Index for market_symbols lookups by symbol (very common operation)
CREATE INDEX idx_market_symbols_symbol ON market_symbols USING btree (symbol);

-- Index for price_data filtering and sorting by timestamp (time series data)
CREATE INDEX idx_price_data_timestamp ON price_data USING brin (timestamp);
CREATE INDEX idx_price_data_symbol_timestamp ON price_data USING btree (symbol_id, timestamp);

-- Index for indicators filtering by type and timestamp
CREATE INDEX idx_indicators_type ON indicators USING btree (indicator_type);
CREATE INDEX idx_indicators_timestamp ON indicators USING brin (timestamp);
CREATE INDEX idx_indicators_symbol_type_time ON indicators USING btree (symbol_id, indicator_type, timestamp);

-- Create a function to automatically update timestamps for audit trail purposes
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.created_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for audit trail on updates
CREATE TRIGGER update_market_symbols_timestamp
BEFORE UPDATE ON market_symbols
FOR EACH ROW EXECUTE FUNCTION update_modified_timestamp();

CREATE TRIGGER update_price_data_timestamp
BEFORE UPDATE ON price_data
FOR EACH ROW EXECUTE FUNCTION update_modified_timestamp();

CREATE TRIGGER update_indicators_timestamp
BEFORE UPDATE ON indicators
FOR EACH ROW EXECUTE FUNCTION update_modified_timestamp();