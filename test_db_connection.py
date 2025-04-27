#!/usr/bin/env python3
"""
Test database connection
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path for importing project modules
sys.path.append(str(Path(__file__).resolve().parent))
from db.connection_manager import ConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('test_db_connection')

def test_database_connection():
    """Test connecting to the database"""
    try:
        logger.info("Creating ConnectionManager instance...")
        conn_manager = ConnectionManager()
        
        logger.info("Testing connection...")
        conn_manager.initialize_pool()
        
        # Try executing a simple query
        logger.info("Executing simple query...")
        query = "SELECT 1 AS test_value"
        results = conn_manager.execute_query(query)
        
        if results and results[0][0] == 1:
            logger.info("Database connection successful!")
            return True
        else:
            logger.error("Query returned unexpected results")
            return False
            
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

def main():
    """Main entry point"""
    print("=== Database Connection Test ===\n")
    
    success = test_database_connection()
    
    if success:
        print("\n✅ Database connection test successful")
        sys.exit(0)
    else:
        print("\n❌ Database connection test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()