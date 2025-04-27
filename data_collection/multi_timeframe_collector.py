#!/usr/bin/env python3
"""
Multi-Timeframe Market Data Collector Module
:TechnologyVersion Python 3.10+
:ArchitecturalPattern :DataPipeline
:Context :DataCollection for market data across multiple timeframes

This module extends the MarketDataCollector to support collecting market data
at multiple timeframes (1min, 5min, 15min, 30min, 60min, 1day) from
Yahoo Finance and stores it in the PostgreSQL database.

It addresses the :Problem of collecting and storing data from different timeframes
while respecting Yahoo Finance API limitations:
- 1-minute data: Limited to 7 days
- 5-minute data: Limited to 60 days
- Hourly data: Limited to 730 days
- Daily data: Available for full history
"""

import os
import sys
import time
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, Set
import pandas as pd

# Add parent directory to path for importing project modules
sys.path.append(str(Path(__file__).parent.parent))
from data_collection.market_data_collector import MarketDataCollector, MarketDataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('multi_timeframe_collector')

class MultiTimeframeMarketDataCollector(MarketDataCollector):
    """
    Extends MarketDataCollector to support collecting market data
    across multiple timeframes with optimized collection strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the multi-timeframe market data collector.
        
        Args:
            config: Optional configuration dictionary. If not provided,
                  uses the project's ConfigManager.
        """
        # Initialize parent class
        super().__init__(config)
        
        # Configure timeframe settings
        self.timeframe_settings = {
            '1min': {
                'yf_interval': '1m',
                'max_days_history': 7,
                'batch_size': 2,  # Process fewer symbols per batch for high-frequency data
                'delay_between_symbols': 2.0  # seconds
            },
            '5min': {
                'yf_interval': '5m',
                'max_days_history': 60,
                'batch_size': 3,
                'delay_between_symbols': 1.5
            },
            '15min': {
                'yf_interval': '15m',
                'max_days_history': 60,
                'batch_size': 5,
                'delay_between_symbols': 1.0
            },
            '30min': {
                'yf_interval': '30m',
                'max_days_history': 60,
                'batch_size': 5,
                'delay_between_symbols': 1.0
            },
            '60min': {
                'yf_interval': '60m',
                'max_days_history': 730,
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
        
        logger.info(f"MultiTimeframeMarketDataCollector initialized with {len(self.timeframe_settings)} timeframes")
    
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
    
    def fetch_ohlcv_data_multi_timeframe(self, symbol: str, timeframe: str, 
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
            
        Raises:
            ValueError: If timeframe is not supported
            MarketDataError: If there's an error collecting data
        """
        # Get timeframe configuration
        tf_config = self.timeframe_settings.get(timeframe)
        if not tf_config:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        yf_interval = tf_config['yf_interval']
        
        # Call the original fetch method with proper interval
        data = self.fetch_ohlcv_data(symbol, start_date, end_date, interval=yf_interval)
        
        # Add timeframe and data_source columns
        if not data.empty:
            data['timeframe'] = timeframe
            data['data_source'] = 'yfinance'
        
        logger.info(f"Fetched {len(data)} rows for {symbol} at {timeframe} timeframe")
        return data
    
    def validate_data_multi_timeframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate the data including timeframe and data_source columns.
        
        Args:
            data: DataFrame with OHLCV data to validate
            
        Returns:
            Validated DataFrame
            
        Raises:
            DataValidationError: If data doesn't conform to schema requirements
        """
        if data.empty:
            return data
            
        logger.info(f"Validating multi-timeframe data with {len(data)} rows")
        
        # First validate using parent class method (handles OHLCV validation)
        data = self.validate_data(data)
        
        # Additional validation for timeframe and data_source
        required_columns = ['timeframe', 'data_source']
        missing_columns = set(required_columns) - set(data.columns)
        if missing_columns:
            raise DataValidationError(f"Missing required timeframe columns: {missing_columns}")
            
        # Ensure timeframe values are valid
        valid_timeframes = set(self.timeframe_settings.keys())
        invalid_timeframes = set(data['timeframe'].unique()) - valid_timeframes
        if invalid_timeframes:
            logger.warning(f"Found invalid timeframes: {invalid_timeframes}")
            # Filter out rows with invalid timeframes
            data = data[data['timeframe'].isin(valid_timeframes)]
            
        return data
    
    def store_ohlcv_data_multi_timeframe(self, data: pd.DataFrame) -> int:
        """
        Store OHLCV data with timeframe and data_source information.
        
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
            
        logger.info(f"Storing {len(data)} rows of multi-timeframe OHLCV data in database")
        
        rows_stored = 0
        
        try:
            # Group data by symbol and timeframe
            for (symbol, timeframe), group in data.groupby(['symbol', 'timeframe']):
                # Get symbol_id
                symbol_id = self.get_symbol_id(symbol)
                
                # Create batch insert query with timeframe and data_source
                insert_query = """
                    INSERT INTO price_data (
                        symbol_id, timestamp, open, high, low, close, volume, 
                        timeframe, data_source
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol_id, timestamp, timeframe, data_source) DO UPDATE 
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
                        # Include timeframe and data_source in parameters
                        params.append((
                            symbol_id,
                            row['timestamp'],
                            row['open'],
                            row['high'],
                            row['low'],
                            row['close'],
                            row['volume'],
                            row['timeframe'],
                            row['data_source']
                        ))
                    
                    # Execute batch insert with transaction
                    with self.connection_manager.transaction() as conn:
                        cursor = conn.cursor()
                        cursor.executemany(insert_query, params)
                        
                    rows_stored += len(batch)
                    logger.debug(f"Stored batch of {len(batch)} rows for {symbol} at {timeframe}")
                
                logger.info(f"Successfully stored {rows_stored} rows for {symbol} at {timeframe}")
                
            return rows_stored
                
        except Exception as e:
            logger.error(f"Error storing multi-timeframe OHLCV data: {e}")
            raise MarketDataError(f"Failed to store multi-timeframe OHLCV data: {e}")
    
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
            
            # Adjust start_date based on timeframe limitations
            if tf_config['max_days_history'] != 'max':
                max_days = tf_config['max_days_history']
                adjusted_start = max(
                    datetime.datetime.strptime(start_date, '%Y-%m-%d'),
                    datetime.datetime.now() - datetime.timedelta(days=max_days)
                ).strftime('%Y-%m-%d')
                logger.info(f"Adjusted start date for {timeframe} from {start_date} to {adjusted_start} "
                           f"(limited to {max_days} days history)")
            else:
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
                        data = self.fetch_ohlcv_data_multi_timeframe(
                            symbol, timeframe, adjusted_start, end_date
                        )
                        
                        # Validate data
                        if not data.empty:
                            data = self.validate_data_multi_timeframe(data)
                            
                            # Store data
                            rows_stored = self.store_ohlcv_data_multi_timeframe(data)
                            
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