#!/usr/bin/env python3
"""
Simple script to test database connection outside of FastAPI.
Run this to debug database connection issues.
"""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlmodel import Session, create_engine

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection with detailed logging."""
    try:
        # Import config
        from src.configs import madcrow_config
        
        logger.info("=== Database Connection Test ===")
        logger.info(f"Host: {madcrow_config.DB_HOST}")
        logger.info(f"Port: {madcrow_config.DB_PORT}")
        logger.info(f"Database: {madcrow_config.DB_DATABASE}")
        logger.info(f"Username: {madcrow_config.DB_USERNAME}")
        logger.info(f"Connection test enabled: {madcrow_config.DB_CONNECTION_TEST_ON_STARTUP}")
        
        # Create engine
        database_url = madcrow_config.sqlalchemy_database_uri
        engine_options = madcrow_config.sqlalchemy_engine_options
        
        logger.info(f"Database URL: {database_url}")
        logger.info(f"Engine options: {engine_options}")
        
        logger.info("Creating database engine...")
        engine = create_engine(
            database_url,
            echo=madcrow_config.SQLALCHEMY_ECHO,
            **engine_options,
        )
        
        logger.info("Testing basic connection...")
        with Session(engine) as session:
            # Test 1: Simple SELECT 1
            logger.info("Test 1: SELECT 1")
            result1 = session.exec(text("SELECT 1")).first()
            logger.info(f"Result: {result1}, Type: {type(result1)}")
            
            # Test 2: SELECT with string
            logger.info("Test 2: SELECT with string")
            result2 = session.exec(text("SELECT 'Database is available' as message")).first()
            logger.info(f"Result: {result2}, Type: {type(result2)}")
            
            # Test 3: Check if accounts table exists
            logger.info("Test 3: Check if accounts table exists")
            try:
                table_check = session.exec(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'accounts'
                    )
                """)).first()
                logger.info(f"Accounts table exists: {table_check}")
                
                if table_check:
                    # Test 4: Query accounts table
                    logger.info("Test 4: Query accounts table")
                    accounts_result = session.exec(text(
                        'SELECT * FROM "public"."accounts" ORDER BY "id" LIMIT 5 OFFSET 0'
                    )).fetchall()
                    logger.info(f"Found {len(accounts_result)} accounts")
                    for i, row in enumerate(accounts_result):
                        logger.info(f"Account {i+1}: {row}")
                else:
                    logger.warning("Accounts table does not exist")
                    
            except Exception as e:
                logger.error(f"Error checking/querying accounts table: {e}")
            
        logger.info("=== All tests completed successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        logger.exception("Full exception details:")
        return False

def test_engine_initialization():
    """Test the database engine initialization from the extension."""
    try:
        logger.info("=== Testing Engine Initialization ===")
        
        from src.extensions.ext_db import db_engine
        
        # Check if engine is initialized
        logger.info(f"Engine initialized: {db_engine._is_initialized}")
        
        if db_engine._is_initialized:
            engine = db_engine.get_engine()
            logger.info(f"Engine: {engine}")
            
            # Test health check
            healthy = db_engine.is_healthy()
            logger.info(f"Engine healthy: {healthy}")
        else:
            logger.warning("Database engine not initialized")
            
    except Exception as e:
        logger.error(f"Engine initialization test failed: {e}")
        logger.exception("Full exception details:")

if __name__ == "__main__":
    print("Testing database connection...")
    
    # Test 1: Direct connection
    success = test_database_connection()
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Engine initialization
    test_engine_initialization()
    
    if success:
        print("\n✅ Database connection test passed!")
    else:
        print("\n❌ Database connection test failed!")
        print("Check the logs above for details.")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running: docker compose -p madcrow up -d db")
        print("2. Check your .env file configuration")
        print("3. Verify the database exists")
