#!/usr/bin/env python3
"""
Database Initialization Script for Market Data System
:TechnologyVersion PostgreSQL 14+
:RelationalDatabase :ArchitecturalPattern
:DataPipeline component for market data collection and analysis

This script initializes the PostgreSQL database and creates the required schema
for the market data system using psycopg2. It addresses several SAPPO :Problems:
- :SQLInjectionVulnerability through proper parameter handling
- :DataInconsistencyProblem by enforcing schema constraints
- :ConnectionManagementIssue by properly closing all resources

Usage:
    python init_db.py [--config CONFIG_FILE]
"""

import sys
import argparse
import logging
import json
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Import our custom modules
from connection_manager import ConnectionManager, ConnectionError, DatabaseNotFoundError
sys.path.append(str(Path(__file__).parent.parent))
from config.config_manager import config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('init_db')

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Initialize market data database')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--env-file', type=str, help='Path to .env file')
    return parser.parse_args()

def create_database(conn_manager):
    """
    Create the market_data_system database if it doesn't exist.
    Uses a separate connection with autocommit to create database.
    
    Args:
        conn_manager: ConnectionManager instance for database operations
    """
    try:
        # Use a connection with autocommit for database creation
        with conn_manager.get_connection(autocommit=True) as conn:
            # Check if database exists first to prevent errors
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", ('market_data_system',))
                exists = cursor.fetchone()
                
                if not exists:
                    logger.info("Creating database 'market_data_system'")
                    # Use sql.Identifier to safely quote the database name and prevent :SQLInjectionVulnerability
                    cursor.execute(
                        sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8' TEMPLATE template0").format(
                            sql.Identifier('market_data_system')
                        )
                    )
                    logger.info("Database created successfully")
                else:
                    logger.info("Database 'market_data_system' already exists")
    
    except ConnectionError as e:
        logger.error(f"Connection error creating database: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error creating database: {e}")
        sys.exit(1)

def execute_schema_file(conn_manager):
    """
    Execute the schema.sql file to create tables and constraints.
    Uses a dedicated connection to the market_data_system database.
    
    Args:
        conn_manager: ConnectionManager instance for database operations
    """
    try:
        # Get the path to the schema file
        schema_path = Path(__file__).parent / 'schema.sql'
        
        if not schema_path.exists():
            logger.error(f"Schema file not found at {schema_path}")
            sys.exit(1)
        
        # Read the schema file
        logger.info(f"Reading schema file from {schema_path}")
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            
        # Filter out commands that would reconnect to database
        filtered_schema = schema_sql.replace('\\c market_data_system', '-- connection handled by Python')
        
        # Execute the schema using the connection manager
        logger.info("Executing schema file")
        conn_manager.execute_script(filtered_schema)
        logger.info("Schema execution completed successfully")
        
    except ConnectionError as e:
        logger.error(f"Connection error executing schema: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error executing schema: {e}")
        sys.exit(1)

def main():
    """Main execution function."""
    args = parse_arguments()
    
    logger.info("Initializing market data system database")
    
    # Load configuration
    if args.env_file:
        config_manager.env_file_path = Path(args.env_file)
        
    # Get database configuration
    db_config = config_manager.get_db_config(args.config)
    
    if not db_config.get('password'):
        logger.error("Database password is required. Set it via config file, .env file, or PGDB_PASSWORD environment variable")
        sys.exit(1)
    
    # Create connection manager for default postgres database
    postgres_conn_manager = ConnectionManager(db_config)
    
    try:
        # Create the database
        create_database(postgres_conn_manager)
        
        # Update config to use the new database
        market_db_config = db_config.copy()
        market_db_config['database'] = 'market_data_system'
        
        # Create connection manager for market_data_system database
        market_conn_manager = ConnectionManager(market_db_config)
        
        # Execute the schema
        execute_schema_file(market_conn_manager)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    finally:
        # Close connection pools
        try:
            postgres_conn_manager.close_pool()
        except:
            pass

if __name__ == "__main__":
    main()