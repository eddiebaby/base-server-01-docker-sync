#!/usr/bin/env python3
"""
File-Based Multi-Timeframe Market Data Collector
:TechnologyVersion Python 3.10+
:ArchitecturalPattern :DataPipeline
:Context :DataCollection for market data across multiple timeframes

This module provides an alternative implementation of the MultiTimeframeMarketDataCollector
that stores data in CSV files instead of a database, allowing for development and testing
without requiring a running PostgreSQL server.
"""

import os
import sys
import time
import logging
import datetime
import pandas as pd
import yfinance as yf
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('file_based_collector')

class FileBasedMultiTimeframeCollector:
    """
    Collects market data at multiple timeframes and stores it in CSV files.
    This serves as a fallback when database connection is not available.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the file-based data collector.
        
        Args:
            data_dir: Directory to store data files. Defaults to '<base_dir>/market_data'.
        """
        # Set up data directory
        if data_dir is None:
            base_dir = Path(__file__).parent.parent
            self.data_dir = os.path.join(base_dir, 'market_data')
        else:
            self.data_dir = data_dir
            
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        logger.info(f"Using data directory: {self.data_dir}")
        
        # Configure timeframe settings based on Yahoo Finance API limitations
        self.timeframe_settings = {
            '1min': {
                'yf_interval': '1m',
                'max_days_history': 7,  # YF limit: 7 days
                'batch_size': 2,
                'delay_between_symbols': 2.0  # seconds
            },
            '5min': {
                'yf_interval': '5m',
                'max_days_history': 60,  # YF limit: 60 days
                'batch_size': 3,
                'delay_between_symbols': 1.5
            },
            '15min': {
                'yf_interval': '15m',
                'max_days_history': 60,  # YF limit: 60 days
                'batch_size': 5,
                'delay_between_symbols': 1.0
            },
            '30min': {
                'yf_interval': '30m',
                'max_days_history': 60,  # YF limit: 60 days
                'batch_size': 5,
                'delay_between_symbols': 1.0
            },
            '60min': {
                'yf_interval': '60m',
                'max_days_history': 730,  # YF limit: 2 years
                'batch_size': 8,
                'delay_between_symbols': 0.5
            },
            '1day': {
                'yf_interval': '1d',
                'max_days_history': 'max',  # All available history
                'batch_size': 10,
                'delay_between_symbols': 0.3
            }
        }
        
        logger.info(f"FileBasedMultiTimeframeCollector initialized with {len(self.timeframe_settings)} timeframes")
    
    def _get_timeframe_priority(self, timeframe: str) -> int:
        """
        Get priority value for timeframe sorting.
        Lower frequency (e.g., daily) gets lower priority value.
        
        Args:
            timeframe: Timeframe string (e.g., '1min', '1day')
            
        Returns:
            Priority value (lower = processed first)
        """
        priority_map = {
            '1day': 0,  # Process daily data first (complete history)
            '60min': 1, 
            '30min': 2,
            '15min': 3,
            '5min': 4,
            '1min': 5   # Process 1-minute data last (highest API burden)
        }
        return priority_map.get(timeframe, 999)
    
    def _get_data_file_path(self, symbol: str, timeframe: str) -> str:
        """
        Get file path for storing data for a symbol and timeframe.
        
        Args:
            symbol: Stock symbol
            timeframe: Timeframe string
            
        Returns:
            Path to the CSV file
        """
        # Create symbol directory if it doesn't exist
        symbol_dir = os.path.join(self.data_dir, symbol.replace('^', ''))
        os.makedirs(symbol_dir, exist_ok=True)
        
        # Return file path
        return os.path.join(symbol_dir, f"{timeframe}.csv")
    
    def fetch_ohlcv_data(self, symbol: str, timeframe: str, 
                         start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch OHLCV data for a specific symbol and timeframe.
        
        Args:
            symbol: Stock symbol to fetch data for
            timeframe: Timeframe string (e.g., '1min', '1day')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            DataFrame with OHLCV data including timeframe and data_source columns
        """
        # Get timeframe configuration
        tf_config = self.timeframe_settings.get(timeframe)
        if not tf_config:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        yf_interval = tf_config['yf_interval']
        
        # Set end date to today if not provided
        if end_date is None:
            end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Fetching {timeframe} data for {symbol} from {start_date} to {end_date}")
        
        try:
            # Initialize ticker
            ticker = yf.Ticker(symbol)
            
            # Fetch data
            data = ticker.history(start=start_date, end=end_date, interval=yf_interval)
            
            if data.empty:
                logger.warning(f"No data returned for {symbol} at {timeframe}")
                return pd.DataFrame()
            
            # Add symbol column if not present
            if 'symbol' not in data.columns:
                data['symbol'] = symbol
                
            # Add timeframe and data_source columns
            data['timeframe'] = timeframe
            data['data_source'] = 'yfinance'
            
            # Reset index to make timestamp a column
            data = data.reset_index()
            
            logger.info(f"Fetched {len(data)} rows for {symbol} at {timeframe}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol} at {timeframe}: {e}")
            return pd.DataFrame()
    
    def validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate the data.
        
        Args:
            data: DataFrame with OHLCV data to validate
            
        Returns:
            Validated DataFrame
        """
        if data.empty:
            return data
            
        logger.info(f"Validating data with {len(data)} rows")
        
        # Check required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = set(required_columns) - set(data.columns)
        if missing_columns:
            logger.warning(f"Missing columns: {missing_columns}")
            # Return empty DataFrame if missing required columns
            return pd.DataFrame()
            
        # Return validated data
        return data
    
    def store_ohlcv_data(self, data: pd.DataFrame) -> int:
        """
        Store OHLCV data in CSV files, optimized for performance.
        
        Args:
            data: DataFrame with validated OHLCV data
            
        Returns:
            Number of rows stored
        """
        if data.empty:
            logger.warning("No data to store")
            return 0
            
        logger.info(f"Storing {len(data)} rows of OHLCV data in CSV files")
        
        rows_stored = 0
        
        try:
            # Group data by symbol and timeframe - more memory efficient than multiple individual groupbys
            grouped_data = data.groupby(['symbol', 'timeframe'])
            
            for (symbol, timeframe), group in grouped_data:
                # Get file path
                file_path = self._get_data_file_path(symbol, timeframe)
                
                # Determine timestamp column name
                timestamp_col = 'Datetime' if 'Datetime' in group.columns else 'Date'
                
                # Check if file exists and optimize merge operation
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    # For large files, use a more efficient approach with chunking
                    if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB threshold
                        self._update_large_file(file_path, group, timestamp_col)
                        logger.info(f"Updated large file {file_path} with {len(group)} new rows")
                    else:
                        # For smaller files, use standard approach but with optimized operations
                        existing_data = pd.read_csv(file_path)
                        
                        # Ensure timestamp column is datetime for proper comparison - only convert once
                        if timestamp_col in existing_data.columns:
                            existing_data[timestamp_col] = pd.to_datetime(existing_data[timestamp_col])
                        
                        # Extract unique timestamps from new data for faster filtering
                        new_timestamps = set(group[timestamp_col])
                        
                        # Filter out rows in existing data that will be replaced
                        if timestamp_col in existing_data.columns:
                            # Use vectorized operations instead of row-by-row operations
                            mask = ~existing_data[timestamp_col].isin(new_timestamps)
                            filtered_existing = existing_data[mask]
                            
                            # Append new data efficiently
                            updated_data = pd.concat([filtered_existing, group], ignore_index=True)
                            
                            # Sort by timestamp - only if needed
                            updated_data = updated_data.sort_values(by=timestamp_col)
                            
                            # Use efficient CSV writing with optimized parameters
                            updated_data.to_csv(file_path, index=False, chunksize=10000)
                            logger.info(f"Updated {file_path} with {len(group)} new rows")
                        else:
                            # Fall back if timestamp column isn't found
                            group.to_csv(file_path, index=False)
                            logger.info(f"Replaced {file_path} with {len(group)} rows")
                else:
                    # Save new data to file with optimized parameters
                    group.to_csv(file_path, index=False, chunksize=10000)
                    logger.info(f"Created {file_path} with {len(group)} rows")
                
                rows_stored += len(group)
                
            return rows_stored
                
        except Exception as e:
            logger.error(f"Error storing OHLCV data: {e}")
            return 0
            
    def _update_large_file(self, file_path: str, new_data: pd.DataFrame, timestamp_col: str) -> None:
        """
        Update a large CSV file efficiently using chunking to avoid loading the entire file into memory.
        
        Args:
            file_path: Path to the CSV file
            new_data: DataFrame containing new data to add
            timestamp_col: Column name containing timestamp
        """
        # Create a temporary file for the updated data
        temp_file = file_path + '.tmp'
        
        # Create a set of timestamps in new data for O(1) lookups
        new_timestamps = set(new_data[timestamp_col])
        
        # Process existing file in chunks to minimize memory usage
        chunk_size = 50000  # Adjust based on available memory
        chunks_written = 0
        
        # Read existing file in chunks
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            # Convert timestamp column to datetime
            if timestamp_col in chunk.columns:
                chunk[timestamp_col] = pd.to_datetime(chunk[timestamp_col])
                
                # Filter out rows that will be replaced by new data
                mask = ~chunk[timestamp_col].isin(new_timestamps)
                filtered_chunk = chunk[mask]
                
                # Write filtered chunk to temp file
                mode = 'w' if chunks_written == 0 else 'a'
                filtered_chunk.to_csv(temp_file, index=False, mode=mode, header=(chunks_written == 0))
                chunks_written += 1
        
        # Append new data to temp file
        new_data.to_csv(temp_file, index=False, mode='a', header=(chunks_written == 0))
        
        # Replace original file with temp file
        os.replace(temp_file, file_path)
    
    def collect_multi_timeframe_data(self, symbols: List[str], timeframes: List[str], 
                                   start_date: str, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect data for multiple symbols across multiple timeframes.
        
        Args:
            symbols: List of symbols to collect data for
            timeframes: List of timeframes to collect data for
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary with collection results and statistics
        """
        logger.info(f"Starting multi-timeframe data collection for {len(symbols)} symbols "
                   f"across {len(timeframes)} timeframes")
        
        results = {
            'symbols_processed': 0,
            'symbols_failed': 0,
            'total_rows_collected': 0,
            'total_rows_stored': 0,
            'timeframe_stats': {},
            'errors': [],
            'started_at': datetime.datetime.now().isoformat(),
            'completed_at': None
        }
        
        # Initialize timeframe stats
        for tf in timeframes:
            results['timeframe_stats'][tf] = {
                'symbols_processed': 0,
                'rows_collected': 0,
                'rows_stored': 0
            }
        
        # Process timeframes from lowest to highest frequency
        # Daily data first, then hourly, then minute-level data
        sorted_timeframes = sorted(
            timeframes,
            key=lambda tf: self._get_timeframe_priority(tf)
        )
        
        for timeframe in sorted_timeframes:
            tf_config = self.timeframe_settings.get(timeframe)
            if not tf_config:
                logger.warning(f"Skipping unsupported timeframe: {timeframe}")
                continue
                
            logger.info(f"Processing {timeframe} timeframe data")
            
            # Adjust start_date based on Yahoo Finance API limitations
            if tf_config['max_days_history'] != 'max':
                max_days = tf_config['max_days_history']
                
                # For intraday data, always use the maximum allowed days from Yahoo Finance API
                # regardless of the requested start_date to avoid API errors
                current_date = datetime.datetime.now()
                # Subtract one day less to account for partial days
                adjusted_start = (current_date - datetime.timedelta(days=max_days-1)).strftime('%Y-%m-%d')
                
                logger.info(f"Adjusted start date for {timeframe} from {start_date} to {adjusted_start} "
                           f"(limited to {max_days} days history per Yahoo Finance API constraints)")
            else:
                # For daily data, we can use the requested start date
                adjusted_start = start_date
                
            batch_size = tf_config['batch_size']
            delay = tf_config['delay_between_symbols']
            
            # Process symbols in batches
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i:i+batch_size]
                logger.info(f"Processing batch of {len(batch_symbols)} symbols for {timeframe}")
                
                # Process each symbol in batch
                for symbol in batch_symbols:
                    try:
                        # Fetch data
                        data = self.fetch_ohlcv_data(symbol, timeframe, adjusted_start, end_date)
                        
                        # Validate data
                        if not data.empty:
                            data = self.validate_data(data)
                            
                            # Store data
                            rows_stored = self.store_ohlcv_data(data)
                            
                            # Update statistics
                            results['symbols_processed'] += 1
                            results['total_rows_collected'] += len(data)
                            results['total_rows_stored'] += rows_stored
                            results['timeframe_stats'][timeframe]['symbols_processed'] += 1
                            results['timeframe_stats'][timeframe]['rows_collected'] += len(data)
                            results['timeframe_stats'][timeframe]['rows_stored'] += rows_stored
                            
                            logger.info(f"Collected and stored {rows_stored} rows for {symbol} at {timeframe}")
                        else:
                            # No data returned
                            logger.warning(f"No data returned for {symbol} at {timeframe}")
                            results['symbols_failed'] += 1
                            results['errors'].append({
                                'symbol': symbol,
                                'timeframe': timeframe,
                                'error': 'No data returned'
                            })
                    except Exception as e:
                        # Handle errors
                        logger.error(f"Error collecting data for {symbol} at {timeframe}: {e}")
                        results['symbols_failed'] += 1
                        results['errors'].append({
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'error': str(e)
                        })
                    
                    # Add delay between symbols to avoid rate limits
                    if delay > 0:
                        time.sleep(delay)
        
        # Calculate success rate
        total_attempts = results['symbols_processed'] + results['symbols_failed']
        if total_attempts > 0:
            results['success_rate'] = round((results['symbols_processed'] / total_attempts) * 100, 2)
        else:
            results['success_rate'] = 0.0
            
        # Return collection results
        results['completed_at'] = datetime.datetime.now().isoformat()
        return results