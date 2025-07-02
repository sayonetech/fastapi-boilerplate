"""Location-related MCP tools."""

from typing import Optional

from fastapi import HTTPException

from src.extensions.ext_mcp import mcp_wrapper
from src.models.location import Location
from src.services.locations import LocationsService

mcp = mcp_wrapper

LOCATION_LIST_DESCRIPTION = (
    "Fetch a list of locations. "
    "You can filter by location name, category, or tag "
    "(which represents facilities and services offered by a location)."
)

@mcp.tool(
    name="get_locations",
    description=LOCATION_LIST_DESCRIPTION,
    tags={"get-locations", "venue-details", "facilities"},
)
async def get_locations(
    name: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
) -> list[Location]:
    """
    Fetch a list of locations, optionally filtered by name, category, or tag.
    - name: Filter locations by name (case-insensitive, substring match).
    - category: Filter locations by category name (case-insensitive, substring match).
    - tag: Filter locations by tag (case-insensitive, substring match).
    """
    try:
        locations_service = LocationsService()
        locations = await locations_service.list_locations()
        filtered = []

        for loc in locations:
            if name and name.lower() not in loc.name.lower():
                continue
            if category and not any(category.lower() in cat.name.lower() for cat in loc.categories):
                continue
            if tag and not any(tag.lower() in t.lower() for t in loc.tags):
                continue
            filtered.append(loc)
        return filtered
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve locations: {str(e)}",
        )
