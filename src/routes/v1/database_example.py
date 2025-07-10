"""Example routes demonstrating database usage patterns with enhanced error handling."""

from ...dependencies import DatabaseSession, OptionalDatabaseSession
from ...exceptions import DatabaseConnectionError, DatabaseError
from ...services.database_example import DatabaseExampleServiceDep
from ...utils.error_factory import ErrorFactory
from ..base_router import BaseRouter
from ..cbv import cbv, get

database_example_router = BaseRouter(prefix="/v1/database", tags=["database-examples"])


@cbv(database_example_router)
class DatabaseExampleController:
    """Example controller demonstrating database usage patterns."""

    @get("/test", operation_id="test_database_connection")
    async def test_connection(
        self,
        session: DatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Test database connection with enhanced error handling."""
        # Early validation - check if session is valid
        if session is None:
            raise DatabaseConnectionError("Database session is not available")

        try:
            is_connected = await service.test_connection(session)

            # Guard clause for failed connection
            if not is_connected:
                raise ErrorFactory.create_database_error(
                    message="Database connection test failed",
                    operation="connection_test",
                )

            # Happy path - return success response
            return {
                "connected": True,
                "message": "Database connection successful",
                "status": "healthy",
            }

        except DatabaseError:
            # Re-raise our custom database errors
            raise
        except Exception as e:
            # Convert unexpected exceptions to our custom error type
            raise ErrorFactory.create_database_error(
                message="Unexpected error during database connection test",
                operation="connection_test",
                cause=e,
            )

    @get("/info", operation_id="get_database_info")
    async def get_database_info(
        self,
        session: DatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Get database information with enhanced error handling."""
        # Early validation
        if session is None:
            raise DatabaseConnectionError("Database session is not available")

        try:
            info = await service.get_database_info(session)

            # Validate response data
            if not info:
                raise ErrorFactory.create_database_error(
                    message="No database information available",
                    operation="get_info",
                )

            return info

        except DatabaseError:
            # Re-raise our custom database errors
            raise
        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Failed to retrieve database information",
                operation="get_info",
                cause=e,
            )

    @get("/optional", operation_id="optional_database_operation")
    async def optional_operation(
        self,
        session: OptionalDatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """
        Example of optional database operation that doesn't fail if DB is unavailable.

        This endpoint demonstrates graceful degradation when database is not available.
        """
        try:
            result = await service.optional_database_operation(session)

            # For optional operations, we don't fail if session is None
            # The service should handle this gracefully
            return result or {
                "status": "unavailable",
                "message": "Database is not available, but operation completed gracefully",
                "data": None,
            }

        except Exception as e:
            # For optional operations, we log the error but return a graceful response
            # instead of raising an exception
            return {
                "status": "error",
                "message": "Optional database operation encountered an error",
                "error": str(e),
                "data": None,
            }

    @get("/accounts", operation_id="get_accounts_sample")
    async def get_accounts_sample(
        self,
        session: DatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Get sample accounts from the database with enhanced error handling."""
        # Early validation
        if session is None:
            raise DatabaseConnectionError("Database session is not available")

        try:
            accounts = await service.get_accounts_sample(session)

            # Validate response data
            if accounts is None:
                raise ErrorFactory.create_database_error(
                    message="No accounts data available",
                    operation="select",
                    table="accounts",
                )

            return accounts

        except DatabaseError:
            # Re-raise our custom database errors
            raise
        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Failed to retrieve accounts sample",
                operation="select",
                table="accounts",
                cause=e,
            )

    @get("/simple-test", operation_id="simple_connection_test")
    async def simple_connection_test(
        self,
        session: DatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Simple database connection test with SELECT 1 and enhanced error handling."""
        # Early validation
        if session is None:
            raise DatabaseConnectionError("Database session is not available")

        try:
            result = await service.simple_connection_test(session)

            # Validate test result
            if not result or not result.get("success"):
                raise ErrorFactory.create_database_error(
                    message="Database connection test failed",
                    operation="connection_test",
                )

            return result

        except DatabaseError:
            # Re-raise our custom database errors
            raise
        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Simple database connection test failed",
                operation="connection_test",
                cause=e,
            )

    @get("/debug", operation_id="debug_query_results")
    async def debug_query_results(
        self,
        session: DatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Debug different query result types with enhanced error handling."""
        # Early validation
        if session is None:
            raise DatabaseConnectionError("Database session is not available")

        try:
            debug_info = await service.debug_query_results(session)

            # Validate debug information
            if not debug_info:
                raise ErrorFactory.create_database_error(
                    message="No debug information available",
                    operation="debug_query",
                )

            return debug_info

        except DatabaseError:
            # Re-raise our custom database errors
            raise
        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Debug query execution failed",
                operation="debug_query",
                cause=e,
            )
