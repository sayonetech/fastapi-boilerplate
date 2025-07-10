"""Example service demonstrating proper database usage patterns."""

import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlmodel import Session

logger = logging.getLogger(__name__)


class DatabaseExampleService:
    """Example service showing database usage patterns."""

    async def test_connection(self, session: Session) -> bool:
        """Test database connection."""
        try:
            result = session.exec(text("SELECT 1")).first()
            logger.info(f"Connection test result: {result}, type: {type(result)}")

            # Handle different result types
            if result is None:
                logger.error("Connection test failed: No result returned")
                return False

            # Convert result to int for comparison
            try:
                result_value = int(result)
                success = result_value == 1
            except (ValueError, TypeError):
                # If result is a tuple/row, try to get first element
                try:
                    if hasattr(result, "__getitem__"):
                        result_value = int(result[0])
                        success = result_value == 1
                    else:
                        # Just check if we got any result
                        success = result is not None
                        logger.info(f"Connection test: Got result {result}, considering it successful")
                except Exception:
                    success = result is not None
                    logger.info(f"Connection test: Got result {result}, considering it successful")

            logger.info(f"Database connection test: {'passed' if success else 'failed'}")
            return success
        except Exception:
            logger.exception("Database connection test failed with exception")
            return False

    async def get_database_info(self, session: Session) -> dict:
        """Get database information."""
        try:
            # Get database version
            version_result = session.exec(text("SELECT version()")).first()
            logger.debug(f"Version result: {version_result}, type: {type(version_result)}")

            # Get current database name
            db_name_result = session.exec(text("SELECT current_database()")).first()
            logger.debug(f"Database name result: {db_name_result}, type: {type(db_name_result)}")

            # Convert Row objects to strings for JSON serialization
            def extract_value(result):
                """Extract value from SQLAlchemy Row object."""
                if result is None:
                    return "Unknown"

                # If it's a Row object or has indexable items, try to get the first value
                if hasattr(result, "__getitem__"):
                    # It's a Row object, tuple, or list - get the first field
                    return str(result[0]) if len(result) > 0 else str(result)
                else:
                    # It's a simple value
                    return str(result)

            version_str = extract_value(version_result)
            db_name_str = extract_value(db_name_result)

            return {"version": version_str, "database_name": db_name_str, "status": "connected"}
        except Exception:
            logger.exception("Failed to get database info")
            raise

    async def optional_database_operation(self, session: Session | None) -> dict:
        """Example of optional database operation."""
        if session is None:
            logger.warning("Database not available for optional operation")
            return {"status": "database_unavailable", "data": None}

        try:
            result = session.exec(text("SELECT 'Database is available' as message")).first()
            logger.debug(f"Optional database operation result: {result}")
            return {"status": "success", "data": str(result) if result else None}
        except Exception as e:
            logger.exception("Optional database operation failed")
            return {"status": "error", "data": str(e)}

    async def get_accounts_sample(self, session: Session) -> dict:
        """Get sample accounts from the database."""
        try:
            result = session.exec(text('SELECT * FROM "public"."accounts" ORDER BY "id" LIMIT 300 OFFSET 0')).fetchall()
            logger.info(f"Retrieved {len(result)} accounts from database")

            # Convert results to dictionaries for JSON serialization
            accounts = []
            for row in result:
                # Convert row to dict - handling different result types
                if hasattr(row, "_asdict"):
                    accounts.append(row._asdict())
                elif hasattr(row, "__dict__"):
                    accounts.append(dict(row.__dict__))
                else:
                    accounts.append(str(row))

            return {"status": "success", "count": len(accounts), "data": accounts}
        except Exception as e:
            logger.exception("Failed to get accounts sample")
            return {"status": "error", "message": str(e), "data": None}

    async def simple_connection_test(self, session: Session) -> dict:
        """Simple connection test with basic SELECT 1."""
        try:
            result = session.exec(text("SELECT 1 as test_value")).first()
            logger.info(f"Simple connection test result: {result}, type: {type(result)}")

            # Also test the raw SELECT 1 without alias
            raw_result = session.exec(text("SELECT 1")).first()
            logger.info(f"Raw SELECT 1 result: {raw_result}, type: {type(raw_result)}")

            return {
                "status": "success",
                "connected": True,
                "test_result_with_alias": str(result),
                "test_result_raw": str(raw_result),
                "result_types": {"with_alias": str(type(result)), "raw": str(type(raw_result))},
            }
        except Exception as e:
            logger.exception("Simple connection test failed")
            return {"status": "error", "connected": False, "message": str(e)}

    async def debug_query_results(self, session: Session) -> dict:
        """Debug different query result types."""
        try:
            results = {}

            # Test different query types
            queries = [
                ("SELECT 1", "basic_select_1"),
                ("SELECT 1 as value", "select_1_with_alias"),
                ("SELECT 'test' as message", "select_string"),
                ("SELECT 1::integer as num", "select_cast_integer"),
                ("SELECT version()", "select_version"),
            ]

            for query, key in queries:
                try:
                    result = session.exec(text(query)).first()

                    # Extract actual value for JSON serialization
                    if hasattr(result, "__getitem__") and hasattr(result, "_fields"):
                        # It's a Row object
                        extracted_value = result[0] if len(result) > 0 else None
                        row_info = {
                            "fields": list(result._fields) if hasattr(result, "_fields") else [],
                            "values": list(result) if hasattr(result, "__iter__") else [result],
                        }
                    elif hasattr(result, "__getitem__"):
                        # It's a tuple or list
                        extracted_value = result[0] if len(result) > 0 else None
                        row_info = {"values": list(result)}
                    else:
                        # It's a simple value
                        extracted_value = result
                        row_info = None

                    results[key] = {
                        "result": str(result),
                        "extracted_value": str(extracted_value) if extracted_value is not None else None,
                        "type": str(type(result)),
                        "repr": repr(result),
                        "row_info": row_info,
                    }
                    logger.info(f"Query '{query}' -> {result} (type: {type(result)})")
                except Exception as e:
                    results[key] = {"error": str(e)}
                    logger.exception("Query failed")

            return {"status": "success", "results": results}

        except Exception as e:
            logger.exception("Debug query results failed")
            return {"status": "error", "message": str(e)}


def get_database_example_service() -> DatabaseExampleService:
    """Dependency to get database example service instance."""
    return DatabaseExampleService()


# Type alias for dependency injection
DatabaseExampleServiceDep = Annotated[DatabaseExampleService, Depends(get_database_example_service)]
