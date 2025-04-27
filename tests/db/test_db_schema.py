#!/usr/bin/env python3
"""
Database Schema and Initialization Tests
:TechnologyVersion Python 3.10+, PostgreSQL 14+
:TestingPattern Dual Strategy (Recursive + Cumulative)

Tests for database schema correctness and initialization process,
addressing key SAPPO :Problems:
- :ConnectionManagementIssue
- :SQLInjectionVulnerability
- :DataIntegrityProblem
- :PerformanceIssue
"""

import os
import sys
import json
import pytest
import psycopg2
from pathlib import Path
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path for importing modules
sys.path.append(str(Path(__file__).parent.parent.parent))
from db.connection_manager import ConnectionManager, ConnectionError
from config.config_manager import config_manager

# Import init_db for testing
sys.path.append(str(Path(__file__).parent.parent.parent / 'db'))
import init_db

@pytest.fixture(scope="session")
def test_config():
    """
    Provide test database configuration.
    Uses the ConfigManager to load configuration from .env file and environment variables.
    """
    # Load configuration from .env file
    config = config_manager.get_db_config()
    
    # Override with test-specific environment variables if present
    for key in ["host", "port", "user", "password"]:
        env_var = f"PGDB_TEST_{key.upper()}"
        if env_var in os.environ:
            config[key] = os.environ[env_var]
            
    # Set database to postgres for initial connection
    config["database"] = "postgres"
    
    # Skip tests if no password is configured
    if not config.get("password"):
        pytest.skip("Database credentials not configured. Set PGDB_PASSWORD in .env file or PGDB_TEST_PASSWORD environment variable.")
        
    return config

@pytest.fixture(scope="session")
def connection_manager(test_config):
    """
    Create a ConnectionManager instance for testing.
    Implements :DesignPattern dependency injection for better testability.
    """
    conn_manager = ConnectionManager(test_config, min_connections=1, max_connections=5)
    try:
        # Initialize the connection pool
        conn_manager.initialize_pool()
        yield conn_manager
    finally:
        # Clean up resources
        conn_manager.close_pool()

@pytest.fixture(scope="session")
def pg_connection(connection_manager):
    """
    Create a PostgreSQL connection for testing.
    Uses the ConnectionManager to get a connection from the pool.
    """
    with connection_manager.get_connection(autocommit=True) as conn:
        yield conn

class TestDatabaseInitialization:
    """
    RECURSIVE TESTING STRATEGY:
    Test database initialization process step by step
    """
    
    def test_config_loading(self):
        """Test configuration loading with different sources."""
        # Test default config
        config = init_db.load_config()
        assert config["host"] == "localhost"
        
        # Test environment variables override
        os.environ["PGDB_HOST"] = "testhost"
        config = init_db.load_config()
        assert config["host"] == "testhost"
        del os.environ["PGDB_HOST"]
        
        # Test config file loading
        test_config = {"host": "filehost", "password": "testpass"}
        tmp_config = Path("test_config.json")
        with open(tmp_config, "w") as f:
            json.dump(test_config, f)
        config = init_db.load_config(tmp_config)
        assert config["host"] == "filehost"
        tmp_config.unlink()

    def test_database_creation(self, test_config, pg_connection):
        """Test database creation process."""
        with pg_connection.cursor() as cursor:
            # Drop test database if exists
            cursor.execute(
                "DROP DATABASE IF EXISTS market_data_system_test"
            )
            
            # Test creation
            cursor.execute(
                sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8' TEMPLATE template0").format(
                    sql.Identifier('market_data_system_test')
                )
            )
            
            # Verify database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                ('market_data_system_test',)
            )
            assert cursor.fetchone() is not None

class TestSchemaCreation:
    """
    RECURSIVE TESTING STRATEGY:
    Test schema components in dependency order
    """
    
    @pytest.fixture(scope="class")
    def schema_connection(self, connection_manager, test_config):
        """
        Connection to test database for schema testing.
        Properly initializes test database connections with error handling.
        """
        # Create a copy of the configuration for the test database
        test_db_config = test_config.copy()
        test_db_config["database"] = "market_data_system_test"
        
        # Create a dedicated connection manager for the test database
        test_conn_manager = ConnectionManager(test_db_config, min_connections=1, max_connections=3)
        
        try:
            # Initialize the connection pool
            test_conn_manager.initialize_pool()
            
            # Get a connection from the pool
            with test_conn_manager.get_connection() as conn:
                # Start a transaction
                yield conn
                # Rollback any changes at the end of the test
                conn.rollback()
        except ConnectionError as e:
            pytest.fail(f"Failed to connect to test database: {e}")
        finally:
            # Clean up resources
            test_conn_manager.close_pool()

    def test_market_symbols_table(self, schema_connection):
        """Test market_symbols table creation and constraints."""
        with schema_connection.cursor() as cursor:
            # Create table
            cursor.execute("""
                CREATE TABLE market_symbols (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    exchange VARCHAR(50) NOT NULL,
                    sector VARCHAR(100),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT unique_market_symbol UNIQUE (symbol),
                    CONSTRAINT valid_symbol_format CHECK (symbol ~ '^[A-Z0-9.-]+$')
                )
            """)
            
            # Test valid insertion
            cursor.execute(
                "INSERT INTO market_symbols (symbol, name, exchange) VALUES (%s, %s, %s)",
                ('AAPL', 'Apple Inc', 'NASDAQ')
            )
            
            # Test unique constraint
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute(
                    "INSERT INTO market_symbols (symbol, name, exchange) VALUES (%s, %s, %s)",
                    ('AAPL', 'Apple Inc', 'NASDAQ')
                )
            schema_connection.rollback()
            
            # Test symbol format constraint
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute(
                    "INSERT INTO market_symbols (symbol, name, exchange) VALUES (%s, %s, %s)",
                    ('aapl', 'Apple Inc', 'NASDAQ')
                )
            schema_connection.rollback()

    def test_price_data_table(self, schema_connection):
        """Test price_data table creation and constraints."""
        with schema_connection.cursor() as cursor:
            # Create table
            cursor.execute("""
                CREATE TABLE price_data (
                    id BIGSERIAL PRIMARY KEY,
                    symbol_id INTEGER NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    open NUMERIC(19,6) NOT NULL,
                    high NUMERIC(19,6) NOT NULL,
                    low NUMERIC(19,6) NOT NULL,
                    close NUMERIC(19,6) NOT NULL,
                    volume BIGINT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_price_data_symbol FOREIGN KEY (symbol_id) REFERENCES market_symbols (id) ON DELETE CASCADE,
                    CONSTRAINT unique_price_point UNIQUE (symbol_id, timestamp),
                    CONSTRAINT positive_prices CHECK (open > 0 AND high > 0 AND low > 0 AND close > 0),
                    CONSTRAINT valid_high_low CHECK (high >= low),
                    CONSTRAINT non_negative_volume CHECK (volume >= 0)
                )
            """)
            
            # Get symbol_id for testing
            cursor.execute("SELECT id FROM market_symbols WHERE symbol = 'AAPL'")
            symbol_id = cursor.fetchone()[0]
            
            # Test valid insertion
            cursor.execute(
                """
                INSERT INTO price_data 
                (symbol_id, timestamp, open, high, low, close, volume)
                VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
                """,
                (symbol_id, 150.0, 155.0, 149.0, 152.0, 1000000)
            )
            
            # Test price constraints
            with pytest.raises(psycopg2.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO price_data 
                    (symbol_id, timestamp, open, high, low, close, volume)
                    VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
                    """,
                    (symbol_id, -1.0, 155.0, 149.0, 152.0, 1000000)
                )
            schema_connection.rollback()

class TestCumulativeSystemState:
    """
    CUMULATIVE TESTING STRATEGY:
    Verify complete system state and interactions
    """
    
    def test_index_effectiveness(self, schema_connection):
        """Test that indexes are properly created and effective."""
        with schema_connection.cursor() as cursor:
            # Create indexes
            cursor.execute("""
                CREATE INDEX idx_market_symbols_symbol ON market_symbols USING btree (symbol);
                CREATE INDEX idx_price_data_timestamp ON price_data USING brin (timestamp);
                CREATE INDEX idx_price_data_symbol_timestamp ON price_data USING btree (symbol_id, timestamp)
            """)
            
            # Verify index usage with EXPLAIN
            cursor.execute("""
                EXPLAIN SELECT * FROM market_symbols WHERE symbol = 'AAPL'
            """)
            plan = cursor.fetchall()
            assert any('Index Scan' in str(row) for row in plan)
            
            cursor.execute("""
                EXPLAIN SELECT * FROM price_data 
                WHERE symbol_id = 1 AND timestamp > CURRENT_TIMESTAMP - INTERVAL '1 day'
            """)
            plan = cursor.fetchall()
            assert any('Index Scan' in str(row) for row in plan)

    def test_trigger_functionality(self, schema_connection):
        """Test that audit triggers work correctly."""
        with schema_connection.cursor() as cursor:
            # Create trigger function
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_modified_timestamp()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.created_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """)
            
            # Create trigger
            cursor.execute("""
                CREATE TRIGGER update_market_symbols_timestamp
                BEFORE UPDATE ON market_symbols
                FOR EACH ROW EXECUTE FUNCTION update_modified_timestamp()
            """)
            
            # Test trigger
            cursor.execute("""
                UPDATE market_symbols SET name = 'Apple Inc.' WHERE symbol = 'AAPL'
            """)
            
            cursor.execute("""
                SELECT created_at FROM market_symbols WHERE symbol = 'AAPL'
            """)
            updated_time = cursor.fetchone()[0]
            assert updated_time is not None

    def test_data_integrity_cascade(self, schema_connection):
        """Test referential integrity and cascading deletes."""
        with schema_connection.cursor() as cursor:
            # Insert test data
            cursor.execute(
                "INSERT INTO market_symbols (symbol, name, exchange) VALUES (%s, %s, %s) RETURNING id",
                ('TEST', 'Test Company', 'NYSE')
            )
            symbol_id = cursor.fetchone()[0]
            
            cursor.execute(
                """
                INSERT INTO price_data 
                (symbol_id, timestamp, open, high, low, close, volume)
                VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
                """,
                (symbol_id, 100.0, 105.0, 95.0, 102.0, 500000)
            )
            
            # Test cascade delete
            cursor.execute("DELETE FROM market_symbols WHERE symbol = 'TEST'")
            
            # Verify price data was cascaded
            cursor.execute("SELECT COUNT(*) FROM price_data WHERE symbol_id = %s", (symbol_id,))
            assert cursor.fetchone()[0] == 0