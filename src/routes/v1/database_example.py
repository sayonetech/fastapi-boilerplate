"""Example routes demonstrating database usage patterns."""

from fastapi import HTTPException

from ...dependencies import DatabaseSession, OptionalDatabaseSession
from ...services.database_example import DatabaseExampleServiceDep
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
        """Test database connection."""
        try:
            is_connected = await service.test_connection(session)
            return {
                "connected": is_connected,
                "message": "Database connection successful" if is_connected else "Database connection failed",
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database test failed: {str(e)}",
            ) from e

    @get("/info", operation_id="get_database_info")
    async def get_database_info(
        self,
        session: DatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Get database information."""
        try:
            return await service.get_database_info(session)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get database info: {str(e)}",
            ) from e

    @get("/optional", operation_id="optional_database_operation")
    async def optional_operation(
        self,
        session: OptionalDatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Example of optional database operation that doesn't fail if DB is unavailable."""
        return await service.optional_database_operation(session)

    @get("/accounts", operation_id="get_accounts_sample")
    async def get_accounts_sample(
        self,
        session: DatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Get sample accounts from the database."""
        try:
            return await service.get_accounts_sample(session)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get accounts: {str(e)}",
            ) from e

    @get("/simple-test", operation_id="simple_connection_test")
    async def simple_connection_test(
        self,
        session: DatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Simple database connection test with SELECT 1."""
        try:
            return await service.simple_connection_test(session)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Simple connection test failed: {str(e)}",
            ) from e

    @get("/debug", operation_id="debug_query_results")
    async def debug_query_results(
        self,
        session: DatabaseSession,
        service: DatabaseExampleServiceDep,
    ) -> dict:
        """Debug different query result types to understand the issue."""
        try:
            return await service.debug_query_results(session)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Debug query failed: {str(e)}",
            ) from e
