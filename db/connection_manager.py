#!/usr/bin/env python3
"""
PostgreSQL Connection Manager
:TechnologyVersion Python 3.10+, PostgreSQL 14+
:DesignPattern Dependency Injection, Connection Pool
:ResourceManagement for database connections

This module implements a connection manager for PostgreSQL databases,
addressing the :ConnectionManagementIssue by providing:
- Connection pooling
- Retry logic for transient errors
- Proper error handling and classification
- Dependency injection for testability
"""

import os
import sys
import time
import logging
import threading
from typing import Dict, List, Optional, Callable, Any
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2 import pool
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path for importing config_manager
sys.path.append(str(Path(__file__).parent.parent))
from config.config_manager import config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('connection_manager')

class ConnectionError(Exception):
    """Base exception for connection-related errors."""
    pass

class ConnectionTimeoutError(ConnectionError):
    """Exception raised when a connection times out."""
    pass

class ConnectionPoolExhaustedError(ConnectionError):
    """Exception raised when the connection pool is exhausted."""
    pass

class DatabaseNotFoundError(ConnectionError):
    """Exception raised when the database does not exist."""
    pass

class ConnectionManager:
    """
    Manages PostgreSQL database connections using connection pooling.
    Implements :ResourceManagement pattern for database connections.
    """
    
    # Class-level storage for connection pools
    _pools: Dict[str, pool.ThreadedConnectionPool] = {}
    _pools_lock = threading.RLock()
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                min_connections: int = 1, max_connections: int = 10):
        """
        Initialize the connection manager.
        
        Args:
            config: Database configuration dictionary
            min_connections: Minimum number of connections in the pool
            max_connections: Maximum number of connections in the pool
        """
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        # Load configuration if not provided
        if config is None:
            self.config = config_manager.get_db_config()
        else:
            self.config = config
            
        # Set default values for retry logic
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        # Initialize connection pool
        self._pool_key = self._get_pool_key(self.config)
        
    def _get_pool_key(self, config: Dict[str, Any]) -> str:
        """
        Generate a unique key for the connection pool based on connection parameters.
        
        Args:
            config: Database configuration dictionary
            
        Returns:
            String key for the connection pool
        """
        return f"{config['host']}:{config['port']}:{config['database']}:{config['user']}"
        
    def initialize_pool(self) -> None:
        """
        Initialize the connection pool if it doesn't exist.
        """
        with self._pools_lock:
            if self._pool_key not in self._pools:
                try:
                    logger.info(f"Initializing connection pool for {self.config['host']}:{self.config['port']}/{self.config['database']}")
                    self._pools[self._pool_key] = pool.ThreadedConnectionPool(
                        self.min_connections,
                        self.max_connections,
                        host=self.config['host'],
                        port=self.config['port'],
                        database=self.config['database'],
                        user=self.config['user'],
                        password=self.config['password']
                    )
                    logger.info("Connection pool initialized successfully")
                except psycopg2.OperationalError as e:
                    if "does not exist" in str(e):
                        raise DatabaseNotFoundError(f"Database {self.config['database']} does not exist") from e
                    else:
                        logger.error(f"Error initializing connection pool: {e}")
                        raise ConnectionError(f"Failed to initialize connection pool: {e}") from e
                except Exception as e:
                    logger.error(f"Unexpected error initializing connection pool: {e}")
                    raise
                    
    def close_pool(self) -> None:
        """
        Close the connection pool.
        """
        with self._pools_lock:
            if self._pool_key in self._pools:
                logger.info(f"Closing connection pool for {self.config['host']}:{self.config['port']}/{self.config['database']}")
                self._pools[self._pool_key].closeall()
                del self._pools[self._pool_key]
                
    @contextmanager
    def get_connection(self, autocommit: bool = False):
        """
        Get a connection from the pool with retry logic.
        
        Args:
            autocommit: Whether to set the connection to autocommit mode
            
        Yields:
            A database connection from the pool
            
        Raises:
            ConnectionTimeoutError: If connection times out after retries
            ConnectionPoolExhaustedError: If the connection pool is exhausted
            ConnectionError: For other connection-related errors
        """
        # Initialize pool if needed
        if self._pool_key not in self._pools:
            self.initialize_pool()
            
        conn = None
        retries = 0
        
        while retries <= self.max_retries:
            try:
                # Get connection from pool
                conn = self._pools[self._pool_key].getconn()
                
                # Set autocommit if requested
                if autocommit:
                    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    
                # Yield connection to caller
                yield conn
                
                # Return connection to pool
                self._pools[self._pool_key].putconn(conn)
                conn = None  # Prevent closing in finally block
                return
                
            except psycopg2.pool.PoolError as e:
                logger.error(f"Connection pool error: {e}")
                raise ConnectionPoolExhaustedError("Connection pool exhausted") from e
                
            except psycopg2.OperationalError as e:
                if "timeout" in str(e).lower() or "could not connect" in str(e).lower():
                    retries += 1
                    if retries <= self.max_retries:
                        wait_time = self.retry_delay * (2 ** (retries - 1))  # Exponential backoff
                        logger.warning(f"Connection attempt {retries} failed, retrying in {wait_time:.2f}s: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Connection failed after {retries} attempts: {e}")
                        raise ConnectionTimeoutError(f"Connection timed out after {retries} attempts") from e
                else:
                    logger.error(f"Database operational error: {e}")
                    raise ConnectionError(f"Database operational error: {e}") from e
                    
            except Exception as e:
                logger.error(f"Unexpected error getting connection: {e}")
                raise
                
        # This should not be reached due to the return in the try block
        # and the raise in the except block, but just in case
        raise ConnectionTimeoutError(f"Connection timed out after {retries} attempts")
        
    @contextmanager
    def transaction(self):
        """
        Execute a transaction with automatic commit/rollback.
        
        Yields:
            A database connection with an active transaction
        """
        with self.get_connection() as conn:
            try:
                # Begin transaction
                yield conn
                # Commit if no exceptions
                conn.commit()
            except Exception:
                # Rollback on exception
                conn.rollback()
                raise
                
    def execute_query(self, query: str, params: Optional[tuple] = None, 
                     autocommit: bool = False) -> List[tuple]:
        """
        Execute a query and return the results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            autocommit: Whether to execute in autocommit mode
            
        Returns:
            List of result tuples
        """
        with self.get_connection(autocommit=autocommit) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:  # Check if query returns results
                    return cursor.fetchall()
                return []
                
    def execute_script(self, script: str, autocommit: bool = False) -> None:
        """
        Execute a SQL script.
        
        Args:
            script: SQL script to execute
            autocommit: Whether to execute in autocommit mode
        """
        with self.get_connection(autocommit=autocommit) as conn:
            with conn.cursor() as cursor:
                cursor.execute(script)
                if not autocommit:
                    conn.commit()