"""
Market Data Storage Module

This module provides a pipeline for storing validated market data in PostgreSQL,
following the Pipe and Filter architectural pattern.

:TechnologyVersion: Python 3.10+
:ArchitecturalPattern: PipeAndFilter
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TypeVar, Generic

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
MarketDataType = Dict[str, Any]  # Type for market data records


class DatabaseError(Exception):
    """Base class for database-related exceptions."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception for database connection issues."""
    pass


class UniqueConstraintViolationError(DatabaseError):
    """Exception for unique constraint violations."""
    pass


class TransactionError(DatabaseError):
    """Exception for transaction-related issues."""
    pass


@dataclass
class StorageResult:
    """Class for storing storage operation results with detailed information."""
    success: bool
    records_processed: int = 0
    records_stored: int = 0
    errors: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize empty list if None provided."""
        if self.errors is None:
            self.errors = []
    
    def add_error(self, filter_name: str, record_id: Any, message: str, exception: Optional[Exception] = None):
        """Add an error with detailed information."""
        self.errors.append({
            'filter': filter_name,
            'record_id': record_id,
            'message': message,
            'exception': str(exception) if exception else None
        })
        self.success = False
    
    def merge(self, other: 'StorageResult'):
        """Merge another StorageResult into this one."""
        self.success = self.success and other.success
        self.records_processed += other.records_processed
        self.records_stored += other.records_stored
        self.errors.extend(other.errors)
        return self


class StorageFilter(ABC, Generic[T]):
    """Abstract base class for storage filters."""
    
    @abstractmethod
    def process(self, data: T) -> StorageResult:
        """Process data synchronously."""
        pass
    
    @abstractmethod
    async def process_async(self, data: T) -> StorageResult:
        """Process data asynchronously."""
        pass


class DataTransformationFilter(StorageFilter[List[MarketDataType]]):
    """Filter for transforming data to match database schema."""
    
    def __init__(self, db_schema: Dict[str, Dict[str, Any]]):
        """
        Initialize with database schema information.
        
        Args:
            db_schema: Dictionary with table schema information
        """
        self.db_schema = db_schema
    
    def process(self, data: List[MarketDataType]) -> Tuple[List[Dict[str, Any]], StorageResult]:
        """
        Transform data to match database schema.
        
        Args:
            data: List of market data records to transform
            
        Returns:
            Tuple of transformed data and StorageResult
        """
        result = StorageResult(success=True)
        transformed_data = []
        
        for i, record in enumerate(data):
            try:
                # Create a new dict with transformed data
                transformed_record = {}
                
                # Apply transformations based on schema
                for field, schema_info in self.db_schema.items():
                    source_field = schema_info.get('source_field', field)
                    
                    if source_field in record:
                        # Apply any field-specific transformations here
                        transformed_record[field] = record[source_field]
                
                transformed_data.append(transformed_record)
                result.records_processed += 1
                
            except Exception as e:
                result.add_error(
                    'DataTransformationFilter',
                    f"record_{i}",
                    f"Failed to transform record {i}: {str(e)}",
                    e
                )
        
        return transformed_data, result
    
    async def process_async(self, data: List[MarketDataType]) -> Tuple[List[Dict[str, Any]], StorageResult]:
        """
        Transform data to match database schema asynchronously.
        
        Args:
            data: List of market data records to transform
            
        Returns:
            Tuple of transformed data and StorageResult
        """
        # Data transformation is CPU-bound, so delegate to sync version
        return await asyncio.to_thread(self.process, data)


class BulkInsertionFilter(StorageFilter[List[Dict[str, Any]]]):
    """Filter for efficiently inserting data in bulk."""
    
    def __init__(self, connection_manager, table_name: str, batch_size: int = 1000):
        """
        Initialize with connection and table information.
        
        Args:
            connection_manager: Database connection manager
            table_name: Name of the target table
            batch_size: Number of records per batch
        """
        self.connection_manager = connection_manager
        self.table_name = table_name
        self.batch_size = batch_size
    
    def _create_insert_query(self, records: List[Dict[str, Any]]) -> Tuple[str, List[Any]]:
        """
        Create an SQL INSERT query and parameters for bulk insertion.
        
        Args:
            records: List of records to insert
            
        Returns:
            Tuple of SQL query string and parameter list
        """
        if not records:
            return "", []
        
        # Get columns from the first record
        columns = list(records[0].keys())
        placeholders = []
        params = []
        
        # Create placeholders and gather parameters
        for record in records:
            # For each record, create a placeholder tuple with the correct number of positional params
            record_placeholders = [f"%s"] * len(columns)
            placeholders.append(f"({', '.join(record_placeholders)})")
            
            # Add values to params list in order
            for col in columns:
                params.append(record.get(col))
        
        # Build the complete query
        query = f"""
        INSERT INTO {self.table_name} ({', '.join(columns)})
        VALUES {', '.join(placeholders)}
        """
        
        return query, params
    
    def _create_upsert_query(self, records: List[Dict[str, Any]], key_columns: List[str]) -> Tuple[str, List[Any]]:
        """
        Create an SQL UPSERT query (INSERT ... ON CONFLICT) and parameters.
        
        Args:
            records: List of records to insert or update
            key_columns: List of column names that form the unique key
            
        Returns:
            Tuple of SQL query string and parameter list
        """
        if not records:
            return "", []
        
        # Get columns from the first record
        columns = list(records[0].keys())
        placeholders = []
        params = []
        
        # Create placeholders and gather parameters
        for record in records:
            # For each record, create a placeholder tuple with the correct number of positional params
            record_placeholders = [f"%s"] * len(columns)
            placeholders.append(f"({', '.join(record_placeholders)})")
            
            # Add values to params list in order
            for col in columns:
                params.append(record.get(col))
        
        # Create the SET clause for updates
        update_columns = [col for col in columns if col not in key_columns]
        set_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])
        
        # Build the complete query
        query = f"""
        INSERT INTO {self.table_name} ({', '.join(columns)})
        VALUES {', '.join(placeholders)}
        ON CONFLICT ({', '.join(key_columns)})
        DO UPDATE SET {set_clause}
        """
        
        return query, params
    
    def process(self, data: List[Dict[str, Any]]) -> StorageResult:
        """
        Insert data into the database in batches.
        
        Args:
            data: List of records to insert
            
        Returns:
            StorageResult with operation status
        """
        result = StorageResult(success=True, records_processed=len(data))
        
        # Process in batches to avoid excessive memory usage
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i+self.batch_size]
            
            try:
                conn = self.connection_manager.get_connection()
                cursor = conn.cursor()
                
                # Create query and execute
                query, params = self._create_insert_query(batch)
                if query:
                    cursor.execute(query, params)
                    result.records_stored += len(batch)
                
                # Note: We don't commit here - that's handled by the transaction filter
                cursor.close()
                
            except Exception as e:
                result.add_error(
                    'BulkInsertionFilter',
                    f"batch_{i//self.batch_size}",
                    f"Failed to insert batch {i//self.batch_size}: {str(e)}",
                    e
                )
                # Don't raise, let the transaction filter handle rollback
        
        return result
    
    async def process_async(self, data: List[Dict[str, Any]]) -> StorageResult:
        """
        Insert data into the database in batches asynchronously.
        
        Args:
            data: List of records to insert
            
        Returns:
            StorageResult with operation status
        """
        # Database operations are I/O-bound, but we'll need to use
        # a proper async database driver for true async behavior.
        # For now, delegate to sync version
        return await asyncio.to_thread(self.process, data)


class TransactionFilter(StorageFilter[List[Dict[str, Any]]]):
    """Filter for managing database transactions."""
    
    def __init__(self, connection_manager):
        """
        Initialize with connection manager.
        
        Args:
            connection_manager: Database connection manager
        """
        self.connection_manager = connection_manager
    
    def process(self, data: List[Dict[str, Any]], previous_filter: StorageFilter) -> StorageResult:
        """
        Wrap the execution of the previous filter in a transaction.
        
        Args:
            data: Data to process
            previous_filter: Filter to execute within the transaction
            
        Returns:
            StorageResult with operation status
        """
        result = StorageResult(success=True)
        
        try:
            conn = self.connection_manager.get_connection()
            
            # Start transaction
            # Note: Auto-commit is typically off by default, so this might not be needed
            # depending on the connection manager implementation
            
            # Execute the wrapped filter
            filter_result = previous_filter.process(data)
            result.merge(filter_result)
            
            # Commit if successful
            if result.success:
                conn.commit()
                logger.info(f"Transaction committed: {result.records_stored} records stored")
            else:
                conn.rollback()
                logger.warning(f"Transaction rolled back due to errors")
                raise TransactionError("Transaction rolled back due to errors")
                
        except Exception as e:
            # Attempt rollback
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {str(rollback_error)}")
            
            result.add_error(
                'TransactionFilter',
                'transaction',
                f"Transaction failed: {str(e)}",
                e
            )
        
        return result
    
    async def process_async(self, data: List[Dict[str, Any]], previous_filter: StorageFilter) -> StorageResult:
        """
        Wrap the execution of the previous filter in a transaction asynchronously.
        
        Args:
            data: Data to process
            previous_filter: Filter to execute within the transaction
            
        Returns:
            StorageResult with operation status
        """
        # For truly async behavior, we'd need an async database driver
        # For now, delegate to sync version
        return await asyncio.to_thread(self.process, data, previous_filter)


class DataStoragePipeline:
    """
    Main storage pipeline class that implements the Pipe and Filter pattern
    for storing validated market data in PostgreSQL.
    """
    
    def __init__(self, connection_manager, config_manager):
        """
        Initialize the pipeline with connection and configuration.
        
        Args:
            connection_manager: Database connection manager
            config_manager: Configuration manager
        """
        self.connection_manager = connection_manager
        self.config_manager = config_manager
        self._init_filters()
    
    def _init_filters(self):
        """Initialize storage filters based on configuration."""
        # Get configuration values
        config = self.config_manager.get_config()
        table_name = config.get('db_table', 'market_data')
        batch_size = config.get('batch_size', 1000)
        
        # Database schema mapping
        db_schema = {
            'symbol': {'source_field': 'symbol'},
            'date': {'source_field': 'date'},
            'open': {'source_field': 'open'},
            'high': {'source_field': 'high'},
            'low': {'source_field': 'low'},
            'close': {'source_field': 'close'},
            'volume': {'source_field': 'volume'},
            'adj_close': {'source_field': 'adj_close'},
            # Add any additional fields and transformations
        }
        
        # Create filters
        self.transformation_filter = DataTransformationFilter(db_schema)
        self.bulk_insertion_filter = BulkInsertionFilter(
            self.connection_manager, table_name, batch_size
        )
        self.transaction_filter = TransactionFilter(self.connection_manager)
    
    def store_data(self, data: List[MarketDataType], max_retries: int = 3) -> StorageResult:
        """
        Store market data in the database with retry logic.
        
        Args:
            data: List of market data records to store
            max_retries: Maximum number of retry attempts
            
        Returns:
            StorageResult with operation status
        """
        result = StorageResult(success=True)
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Step 1: Transform data to match database schema
                transformed_data, transform_result = self.transformation_filter.process(data)
                result.merge(transform_result)
                
                # Short-circuit if transformation failed
                if not result.success:
                    return result
                
                # Step 2 & 3: Insert data within a transaction
                storage_result = self.transaction_filter.process(
                    transformed_data, self.bulk_insertion_filter
                )
                result.merge(storage_result)
                
                # If successful, we're done
                if result.success:
                    return result
                
                # Check if we should retry based on the error type
                should_retry = False
                for error in result.errors:
                    exception_str = error.get('exception', '')
                    if 'connection' in exception_str.lower():
                        # Retry on connection issues
                        should_retry = True
                        break
                
                if not should_retry:
                    # No retryable errors, exit loop
                    return result
                
                # Retry after a delay
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.warning(f"Retrying operation after {wait_time} seconds (attempt {retry_count}/{max_retries})")
                    time.sleep(wait_time)
                    
                    # Reset result for retry
                    result = StorageResult(success=True)
                else:
                    logger.error(f"Max retries ({max_retries}) exceeded")
                    
            except Exception as e:
                result.add_error(
                    'DataStoragePipeline',
                    'pipeline',
                    f"Unhandled exception in storage pipeline: {str(e)}",
                    e
                )
                return result
        
        return result
    
    async def store_data_async(self, data: List[MarketDataType], max_retries: int = 3) -> StorageResult:
        """
        Store market data in the database with retry logic asynchronously.
        
        Args:
            data: List of market data records to store
            max_retries: Maximum number of retry attempts
            
        Returns:
            StorageResult with operation status
        """
        result = StorageResult(success=True)
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Step 1: Transform data to match database schema
                transformed_data, transform_result = await self.transformation_filter.process_async(data)
                result.merge(transform_result)
                
                # Short-circuit if transformation failed
                if not result.success:
                    return result
                
                # Step 2 & 3: Insert data within a transaction
                # Note: Using await with process_async
                storage_result = await self.transaction_filter.process_async(
                    transformed_data, self.bulk_insertion_filter
                )
                result.merge(storage_result)
                
                # If successful, we're done
                if result.success:
                    return result
                
                # Check if we should retry based on the error type
                should_retry = False
                for error in result.errors:
                    exception_str = error.get('exception', '')
                    if 'connection' in exception_str.lower():
                        # Retry on connection issues
                        should_retry = True
                        break
                
                if not should_retry:
                    # No retryable errors, exit loop
                    return result
                
                # Retry after a delay
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.warning(f"Retrying operation after {wait_time} seconds (attempt {retry_count}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    
                    # Reset result for retry
                    result = StorageResult(success=True)
                else:
                    logger.error(f"Max retries ({max_retries}) exceeded")
                    
            except Exception as e:
                result.add_error(
                    'DataStoragePipeline',
                    'pipeline',
                    f"Unhandled exception in storage pipeline: {str(e)}",
                    e
                )
                return result
        
        return result
    
    def handle_unique_constraint_violation(self, data: List[MarketDataType], key_columns: List[str]) -> StorageResult:
        """
        Handle unique constraint violations by using upsert functionality.
        
        Args:
            data: List of market data records to store
            key_columns: List of column names that form the unique key
            
        Returns:
            StorageResult with operation status
        """
        result = StorageResult(success=True)
        
        try:
            # Step 1: Transform data to match database schema
            transformed_data, transform_result = self.transformation_filter.process(data)
            result.merge(transform_result)
            
            # Short-circuit if transformation failed
            if not result.success:
                return result
            
            # Get configuration values
            config = self.config_manager.get_config()
            table_name = config.get('db_table', 'market_data')
            batch_size = config.get('batch_size', 1000)
            
            # Process in batches
            for i in range(0, len(transformed_data), batch_size):
                batch = transformed_data[i:i+batch_size]
                
                try:
                    conn = self.connection_manager.get_connection()
                    cursor = conn.cursor()
                    
                    # Create UPSERT query and execute
                    query, params = self.bulk_insertion_filter._create_upsert_query(batch, key_columns)
                    if query:
                        cursor.execute(query, params)
                        result.records_stored += len(batch)
                        result.records_processed += len(batch)
                    
                    conn.commit()
                    cursor.close()
                    
                except Exception as e:
                    # Attempt rollback
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    
                    result.add_error(
                        'UniqueConstraintHandler',
                        f"batch_{i//batch_size}",
                        f"Failed to upsert batch {i//batch_size}: {str(e)}",
                        e
                    )
            
        except Exception as e:
            result.add_error(
                'UniqueConstraintHandler',
                'handler',
                f"Unhandled exception in unique constraint handler: {str(e)}",
                e
            )
        
        return result
    
    async def handle_unique_constraint_violation_async(self, data: List[MarketDataType], key_columns: List[str]) -> StorageResult:
        """
        Handle unique constraint violations by using upsert functionality asynchronously.
        
        Args:
            data: List of market data records to store
            key_columns: List of column names that form the unique key
            
        Returns:
            StorageResult with operation status
        """
        # For now, delegate to sync version
        return await asyncio.to_thread(self.handle_unique_constraint_violation, data, key_columns)