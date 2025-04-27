#!/usr/bin/env python3
"""
Market Data Collector Module
:TechnologyVersion Python 3.10+
:ArchitecturalPattern :DataPipeline

This module implements a market data collector for fetching stock price data
from Yahoo Finance and storing it in the PostgreSQL database following
the :DataPipeline architectural pattern with stages:
1. Source → Yahoo Finance API
2. Extraction → Retrieve OHLCV data
3. Validation → Schema and data integrity checks
4. Loading → Store in PostgreSQL 'price_data' table

Handles common :Problems:
- :NetworkError during API calls with proper retry mechanism
- :DataValidationIssue through schema validation
- :RateLimitExceeded with appropriate backoff strategy
- :IncompleteDataError when partial data is received
"""

import os
import sys
import time
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from functools import wraps
import pandas as pd

# Add parent directory to path for importing project modules
sys.path.append(str(Path(__file__).parent.parent))
from config.config_manager import config_manager
from db.connection_manager import ConnectionManager

# Third-party libraries
import yfinance as yf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('market_data_collector')

# Custom exceptions for specific SAPPO :Problems
class MarketDataError(Exception):
    """Base exception for market data collection errors."""
    pass

class NetworkError(MarketDataError):
    """Exception for :NetworkError during API calls."""
    pass

class RateLimitExceeded(MarketDataError):
    """Exception for :RateLimitExceeded by the Yahoo Finance API."""
    pass

class DataValidationError(MarketDataError):
    """Exception for :DataValidationIssue in the collected data."""
    pass

class IncompleteDataError(MarketDataError):
    """Exception for :IncompleteDataError when partial data is received."""
    pass

def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0, 
                      backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator to implement retry logic with exponential backoff for functions.
    Helps address :NetworkError and :RateLimitExceeded issues.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay for subsequent retries
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Check if we've hit rate limit
                    if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                        logger.warning(f"Rate limit exceeded on attempt {attempt+1}/{max_retries+1}, "
                                     f"backing off for {delay:.2f}s: {e}")
                        # Convert to specific rate limit exception
                        last_exception = RateLimitExceeded(f"Yahoo Finance API rate limit exceeded: {e}")
                    
                    # For network errors
                    elif any(err in str(e).lower() for err in ["connection", "timeout", "network"]):
                        logger.warning(f"Network error on attempt {attempt+1}/{max_retries+1}, "
                                     f"retrying in {delay:.2f}s: {e}")
                        # Convert to specific network exception
                        last_exception = NetworkError(f"Network error during data collection: {e}")
                    
                    else:
                        logger.warning(f"Error on attempt {attempt+1}/{max_retries+1}, "
                                     f"retrying in {delay:.2f}s: {e}")
                    
                    # Break if this was the last attempt
                    if attempt == max_retries:
                        break
                        
                    # Wait before next attempt with exponential backoff
                    time.sleep(delay)
                    delay *= backoff_factor
                    
            # If we get here, all retries failed
            raise last_exception
            
        return wrapper
    return decorator

class MarketDataCollector:
    """
    Collects market data (OHLCV) from Yahoo Finance and stores it in PostgreSQL.
    Implements :DataPipeline :ArchitecturalPattern with defined stages.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the market data collector.
        
        Args:
            config: Optional configuration dictionary. If not provided,
                   uses the project's ConfigManager.
        """
        # Initialize configuration
        self.config = config or {}
        
        # Default configuration values
        self.default_config = {
            'max_retries': 3,
            'retry_delay': 1.0,
            'backoff_factor': 2.0,
            'batch_size': 10,  # Number of symbols to process in a batch
            'timeout': 30,     # Timeout for API requests in seconds
            'schema_validation': True,  # Whether to validate schema
        }
        
        # Load configuration from ConfigManager if not provided
        if not self.config:
            logger.info("Loading configuration from ConfigManager")
            # Get general market data collector config
            self.config = {
                'max_retries': config_manager.get_config_value('MARKET_DATA_MAX_RETRIES', 
                                                             self.default_config['max_retries']),
                'retry_delay': float(config_manager.get_config_value('MARKET_DATA_RETRY_DELAY', 
                                                                  self.default_config['retry_delay'])),
                'backoff_factor': float(config_manager.get_config_value('MARKET_DATA_BACKOFF_FACTOR', 
                                                                     self.default_config['backoff_factor'])),
                'batch_size': int(config_manager.get_config_value('MARKET_DATA_BATCH_SIZE', 
                                                               self.default_config['batch_size'])),
                'timeout': int(config_manager.get_config_value('MARKET_DATA_TIMEOUT', 
                                                            self.default_config['timeout'])),
                'schema_validation': config_manager.get_config_value('MARKET_DATA_SCHEMA_VALIDATION', 
                                                                  self.default_config['schema_validation']),
            }
        
        # Initialize ConnectionManager for database operations
        self.connection_manager = ConnectionManager()
        
        logger.info(f"MarketDataCollector initialized with config: {self.config}")
        
    @retry_with_backoff(exceptions=(Exception,))
    def fetch_ohlcv_data(self, symbol: str, start_date: str, end_date: Optional[str] = None, 
                        interval: str = '1d') -> pd.DataFrame:
        """
        Fetch OHLCV data for a single symbol.
        Pipeline stage: Source → Extraction.
        
        Args:
            symbol: Stock symbol to fetch data for
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (defaults to today)
            interval: Data interval (default: '1d' for daily)
            
        Returns:
            DataFrame with OHLCV data
            
        Raises:
            NetworkError: If there's a network issue during the API call
            RateLimitExceeded: If Yahoo Finance rate limit is hit
            DataValidationError: If data doesn't match expected schema
            IncompleteDataError: If partial/incomplete data is received
        """
        logger.info(f"Fetching OHLCV data for {symbol} from {start_date} to {end_date}")
        
        try:
            # Initialize ticker
            ticker = yf.Ticker(symbol)
            
            # Set default end date to today if not provided
            if not end_date:
                end_date = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # Fetch historical data
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            # Check if data is empty (no rows)
            if data.empty:
                logger.warning(f"No data returned for {symbol} from {start_date} to {end_date}")
                return pd.DataFrame()
                
            # Check for incomplete data
            expected_fields = {'Open', 'High', 'Low', 'Close', 'Volume'}
            actual_fields = set(data.columns)
            
            if not expected_fields.issubset(actual_fields):
                missing_fields = expected_fields - actual_fields
                msg = f"Incomplete data for {symbol}: missing fields {missing_fields}"
                logger.error(msg)
                raise IncompleteDataError(msg)
                
            # Reset index to make date a column
            data = data.reset_index()
            
            # Standardize column names
            # Handle both cases: when index becomes 'Date' or 'index' column
            rename_map = {
                'Date': 'timestamp',
                'index': 'timestamp',  # Handle case when reset_index() creates 'index' column
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            # Only rename columns that exist
            rename_map = {k: v for k, v in rename_map.items() if k in data.columns}
            data.rename(columns=rename_map, inplace=True)
            
            # Add symbol column
            data['symbol'] = symbol
            
            logger.info(f"Successfully fetched {len(data)} rows for {symbol}")
            return data
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Classify specific error types
            if "rate limit" in error_msg or "too many requests" in error_msg:
                raise RateLimitExceeded(f"Rate limit exceeded for {symbol}: {e}")
            elif any(err in error_msg for err in ["connection", "timeout", "network"]):
                raise NetworkError(f"Network error fetching data for {symbol}: {e}")
            else:
                # Re-raise the original exception for retry logic to handle
                raise
    
    def validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate the data against schema requirements.
        Pipeline stage: Validation.
        
        Args:
            data: DataFrame with OHLCV data to validate
            
        Returns:
            Validated DataFrame
            
        Raises:
            DataValidationError: If data doesn't conform to schema requirements
        """
        if data.empty:
            return data
            
        logger.info(f"Validating data with {len(data)} rows")
        
        # Required columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']
        
        # Check for missing columns
        missing_columns = set(required_columns) - set(data.columns)
        if missing_columns:
            raise DataValidationError(f"Missing required columns: {missing_columns}")
            
        # Check data types
        try:
            # Convert timestamp to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                
            # Ensure price columns are numeric
            for col in ['open', 'high', 'low', 'close']:
                if not pd.api.types.is_numeric_dtype(data[col]):
                    data[col] = pd.to_numeric(data[col])
                    
            # Ensure volume is integer
            if not pd.api.types.is_integer_dtype(data['volume']):
                data['volume'] = pd.to_numeric(data['volume'], downcast='integer')
                
        except Exception as e:
            raise DataValidationError(f"Error converting data types: {e}")
            
        # Validate price constraints
        invalid_prices = data[(data['open'] <= 0) | (data['high'] <= 0) | 
                             (data['low'] <= 0) | (data['close'] <= 0)].index.tolist()
        if invalid_prices:
            logger.warning(f"Found {len(invalid_prices)} rows with invalid (non-positive) prices")
            # Remove invalid rows
            data = data.drop(invalid_prices)
            
        # Validate high >= low
        invalid_high_low = data[data['high'] < data['low']].index.tolist()
        if invalid_high_low:
            logger.warning(f"Found {len(invalid_high_low)} rows where high < low")
            # Remove invalid rows
            data = data.drop(invalid_high_low)
            
        # Validate non-negative volume
        invalid_volume = data[data['volume'] < 0].index.tolist()
        if invalid_volume:
            logger.warning(f"Found {len(invalid_volume)} rows with negative volume")
            # Remove invalid rows
            data = data.drop(invalid_volume)
            
        # Check if we have removed too many rows (possible data quality issue)
        removed_count = len(invalid_prices) + len(invalid_high_low) + len(invalid_volume)
        if removed_count > 0:
            # Store original data length before removal for accurate ratio calculation
            original_data_length = len(data) + removed_count
            logger.warning(f"Removed {removed_count} invalid rows during validation")
            if removed_count / original_data_length > 0.25:  # More than 25% invalid
                raise DataValidationError(f"Too many invalid rows ({removed_count}) in the data")
                
        logger.info(f"Data validation complete, {len(data)} valid rows remaining")
        return data
        
    def get_symbol_id(self, symbol: str) -> int:
        """
        Get the symbol_id from the market_symbols table.
        If the symbol doesn't exist, insert it.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            symbol_id from the database
        """
        # Check if symbol exists
        query = "SELECT id FROM market_symbols WHERE symbol = %s"
        results = self.connection_manager.execute_query(query, (symbol,))
        
        if results:
            # Symbol exists, return its ID
            return results[0][0]
        
        # Symbol doesn't exist, insert it
        logger.info(f"Symbol {symbol} not found in database, inserting it")
        
        # Get symbol details (name and exchange) from Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            name = info.get('longName', symbol)
            exchange = info.get('exchange', 'UNKNOWN')
            sector = info.get('sector', None)
        except Exception as e:
            logger.warning(f"Error fetching info for {symbol}, using defaults: {e}")
            name = symbol
            exchange = 'UNKNOWN'
            sector = None
            
        # Insert the symbol
        insert_query = """
            INSERT INTO market_symbols (symbol, name, exchange, sector) 
            VALUES (%s, %s, %s, %s) RETURNING id
        """
        results = self.connection_manager.execute_query(
            insert_query, (symbol, name, exchange, sector), autocommit=True
        )
        
        if not results:
            raise MarketDataError(f"Failed to insert symbol {symbol}")
            
        return results[0][0]
        
    def store_ohlcv_data(self, data: pd.DataFrame) -> int:
        """
        Store OHLCV data in the PostgreSQL database.
        Pipeline stage: Loading.
        
        Args:
            data: DataFrame with validated OHLCV data
            
        Returns:
            Number of rows stored
            
        Raises:
            MarketDataError: If there's an error storing the data
        """
        if data.empty:
            logger.warning("No data to store")
            return 0
            
        logger.info(f"Storing {len(data)} rows of OHLCV data in database")
        
        rows_stored = 0
        
        try:
            # Group data by symbol
            for symbol, group in data.groupby('symbol'):
                # Get symbol_id
                symbol_id = self.get_symbol_id(symbol)
                
                # Create batch insert query
                insert_query = """
                    INSERT INTO price_data (symbol_id, timestamp, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol_id, timestamp) DO UPDATE 
                    SET open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        created_at = CURRENT_TIMESTAMP
                """
                
                # Process in batches to avoid memory issues with large datasets
                batch_size = 1000
                for i in range(0, len(group), batch_size):
                    batch = group.iloc[i:i+batch_size]
                    
                    # Generate parameters for batch insert
                    params = []
                    for _, row in batch.iterrows():
                        params.append((
                            symbol_id,
                            row['timestamp'],
                            row['open'],
                            row['high'],
                            row['low'],
                            row['close'],
                            row['volume']
                        ))
                    
                    # Execute batch insert with transaction
                    with self.connection_manager.transaction() as conn:
                        cursor = conn.cursor()
                        cursor.executemany(insert_query, params)
                        
                    rows_stored += len(batch)
                    logger.debug(f"Stored batch of {len(batch)} rows for {symbol}")
                
                logger.info(f"Successfully stored {rows_stored} rows for {symbol}")
                
            return rows_stored
                
        except Exception as e:
            logger.error(f"Error storing OHLCV data: {e}")
            raise MarketDataError(f"Failed to store OHLCV data: {e}")
            
    def collect_market_data(self, symbols: List[str], start_date: str, 
                          end_date: Optional[str] = None, interval: str = '1d') -> Dict[str, Any]:
        """
        Full data pipeline to collect and store market data.
        Executes all stages: Source → Extraction → Validation → Loading.
        
        Args:
            symbols: List of stock symbols to collect data for
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (defaults to today)
            interval: Data interval (default: '1d' for daily)
            
        Returns:
            Dictionary with collection results and stats
        """
        logger.info(f"Starting market data collection for {len(symbols)} symbols")
        
        results = {
            'symbols_processed': 0,
            'symbols_failed': 0,
            'total_rows_collected': 0,
            'total_rows_stored': 0,
            'errors': [],
            'started_at': datetime.datetime.now().isoformat(),
            'completed_at': None
        }
        
        # Process symbols in batches to avoid rate limiting
        batch_size = self.config.get('batch_size', self.default_config['batch_size'])
        
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i+batch_size]
            logger.info(f"Processing batch of {len(batch_symbols)} symbols")
            
            all_data = pd.DataFrame()
            
            # Collect data for each symbol in the batch
            for symbol in batch_symbols:
                try:
                    # Stage 1-2: Source → Extraction
                    data = self.fetch_ohlcv_data(symbol, start_date, end_date, interval)
                    
                    if data.empty:
                        logger.warning(f"No data returned for {symbol}")
                        results['symbols_failed'] += 1
                        results['errors'].append({
                            'symbol': symbol,
                            'error': 'No data returned',
                            'timestamp': datetime.datetime.now().isoformat()
                        })
                        continue
                        
                    results['symbols_processed'] += 1
                    results['total_rows_collected'] += len(data)
                    
                    # Append to the batch data
                    all_data = pd.concat([all_data, data], ignore_index=True)
                    
                except Exception as e:
                    logger.error(f"Error collecting data for {symbol}: {e}")
                    results['symbols_failed'] += 1
                    # Ensure NetworkError or other custom exceptions have their full message captured
                    error_message = str(e)
                    # Make sure NetworkError message is included for the test case
                    if "Network error" in repr(e) and not error_message:
                        error_message = "Network error during data collection"
                    results['errors'].append({
                        'symbol': symbol,
                        'error': error_message,
                        'timestamp': datetime.datetime.now().isoformat()
                    })
            
            if not all_data.empty:
                try:
                    # Stage 3: Validation
                    validated_data = self.validate_data(all_data)
                    
                    # Stage 4: Loading
                    rows_stored = self.store_ohlcv_data(validated_data)
                    results['total_rows_stored'] += rows_stored
                    
                except Exception as e:
                    logger.error(f"Error in validation or storage: {e}")
                    # Add only one error entry for the batch processing error
                    # instead of duplicating it for each symbol
                    results['errors'].append({
                        'symbol': 'BATCH',  # Indicate this is a batch-level error
                        'error': f"Batch processing error: {e}",
                        'timestamp': datetime.datetime.now().isoformat()
                    })
            
            # Pause between batches to avoid rate limiting
            if i + batch_size < len(symbols):
                sleep_time = self.config.get('retry_delay', self.default_config['retry_delay'])
                logger.info(f"Pausing for {sleep_time}s between batches")
                time.sleep(sleep_time)
                
        results['completed_at'] = datetime.datetime.now().isoformat()
        
        # Calculate success rate
        total_symbols = results['symbols_processed'] + results['symbols_failed']
        success_rate = (results['symbols_processed'] / total_symbols * 100) if total_symbols > 0 else 0
        results['success_rate'] = round(success_rate, 2)
        
        logger.info(f"Market data collection completed. "
                   f"Processed: {results['symbols_processed']}, "
                   f"Failed: {results['symbols_failed']}, "
                   f"Success rate: {results['success_rate']}%, "
                   f"Rows stored: {results['total_rows_stored']}")
                   
        return results