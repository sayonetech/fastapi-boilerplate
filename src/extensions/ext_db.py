import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import create_engine, Session

from ..beco_app import BecoApp
from ..configs import madcrow_config

logger = logging.getLogger(__name__)


class DBEngine:
    """Database engine manager with proper lifecycle and error handling."""

    def __init__(self):
        self._engine: Optional[Engine] = None
        self._is_initialized = False

    def init_app(self, app: BecoApp) -> None:
        """Initialize database engine with proper error handling and logging."""
        try:
            logger.info("Initializing database engine...")

            # Use the DatabaseConfig from madcrow_config
            db_config = madcrow_config

            # Create database URL using the configuration
            database_url = db_config.sqlalchemy_database_uri
            engine_options = db_config.sqlalchemy_engine_options

            logger.info(f"Connecting to database: {db_config.DB_HOST}:{db_config.DB_PORT}/{db_config.DB_DATABASE}")
            logger.debug(f"Engine options: {engine_options}")

            self._engine = create_engine(
                database_url,
                echo=db_config.SQLALCHEMY_ECHO,
                **engine_options,
            )

            # Test the connection if enabled
            print("inside init app")
            print(db_config.DB_CONNECTION_TEST_ON_STARTUP)
            if db_config.DB_CONNECTION_TEST_ON_STARTUP:
                connection_test_passed = self._test_connection()

                if not connection_test_passed:
                    if madcrow_config.DEPLOY_ENV == "PRODUCTION":
                        raise RuntimeError("Database connection test failed in production environment")
                    else:
                        logger.warning("Database connection test failed, but continuing in development mode")
            else:
                logger.info("Database connection test skipped (disabled in configuration)")

            # Store engine on app for global access
            app.state.engine = self._engine
            self._is_initialized = True

            logger.info("Database engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            if madcrow_config.DEPLOY_ENV == "PRODUCTION":
                raise RuntimeError(f"Database initialization failed: {e}") from e
            else:
                logger.warning(f"Database initialization failed in development mode: {e}")
                # Still mark as initialized to allow the app to start
                self._is_initialized = True
                if self._engine:
                    app.state.engine = self._engine

    def _test_connection(self) -> bool:
        """Test database connection during initialization."""
        print("OK")
        if not self._engine:
            logger.error("Cannot test connection: Engine not initialized")
            return False

        try:
            logger.debug("Testing database connection...")
            with Session(self._engine) as session:
                # Simple connection test
                result = session.exec(text("SELECT 1")).first()
                logger.debug(f"Connection test result: {result}, type: {type(result)}")

                # Handle different result types more robustly
                if result is None:
                    logger.error("Database connection test failed: No result returned")
                    return False

                # Try to convert to int for comparison
                try:
                    result_value = int(result)
                    success = result_value == 1
                except (ValueError, TypeError):
                    # If result is a tuple/row, try to get first element
                    try:
                        if hasattr(result, '__getitem__'):
                            result_value = int(result[0])
                            success = result_value == 1
                        else:
                            # Just check if we got any result
                            success = True
                            logger.debug(f"Got non-integer result {result}, considering successful")
                    except:
                        success = True
                        logger.debug(f"Got result {result}, considering successful")

                if success:
                    logger.info("Database connection test passed")
                else:
                    logger.error(f"Database connection test failed: unexpected result {result}")

                return success
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            logger.debug(f"Connection details: {madcrow_config.DB_HOST}:{madcrow_config.DB_PORT}/{madcrow_config.DB_DATABASE}")
            return False

    def get_engine(self) -> Engine:
        """Get the database engine with validation."""
        if not self._is_initialized or not self._engine:
            raise RuntimeError("Database engine not initialized. Call init_app() first.")
        return self._engine

    def is_healthy(self) -> bool:
        """Check if database connection is healthy."""
        if not self._is_initialized or not self._engine:
            logger.debug("Database health check: engine not initialized")
            return False

        try:
            with Session(self._engine) as session:
                result = session.exec(text("SELECT 1")).first()
                logger.debug(f"Health check result: {result}, type: {type(result)}")

                # Handle different result types
                if result is None:
                    logger.warning("Database health check: No result returned")
                    return False

                # Try to convert to int for comparison
                try:
                    result_value = int(result)
                    healthy = result_value == 1
                except (ValueError, TypeError):
                    # If result is a tuple/row, try to get first element
                    try:
                        if hasattr(result, '__getitem__'):
                            result_value = int(result[0])
                            healthy = result_value == 1
                        else:
                            # Just check if we got any result
                            healthy = True
                            logger.debug(f"Health check: Got result {result}, considering healthy")
                    except:
                        healthy = True
                        logger.debug(f"Health check: Got result {result}, considering healthy")

                if healthy:
                    logger.debug("Database health check: passed")
                else:
                    logger.warning(f"Database health check: failed - unexpected result {result}")
                return healthy
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    def close(self) -> None:
        """Close database engine and cleanup resources."""
        if self._engine:
            logger.info("Closing database engine...")
            self._engine.dispose()
            self._engine = None
            self._is_initialized = False
            logger.info("Database engine closed")


db_engine = DBEngine()


def is_enabled() -> bool:
    """Check if database extension should be enabled."""
    return True  # Database is always required


def init_app(app: BecoApp) -> None:
    """Initialize database extension with proper error handling."""
    try:
        db_engine.init_app(app)
        logger.info("Database extension initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database extension: {e}")
        raise


def cleanup() -> None:
    """Cleanup database resources. Called by lifespan manager."""
    db_engine.close()
