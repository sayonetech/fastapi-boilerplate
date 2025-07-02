"""Location information routes."""

from fastapi import APIRouter, HTTPException

from ..models.location import Location
from ..services.locations import LocationsServiceDep

locations_router = APIRouter()


@locations_router.get(
    "/list",
    operation_id="list_locations",
    response_model=list[Location],
    description="Get a list of all available locations.",
)
async def list_locations(
    locations_service: LocationsServiceDep,
) -> list[Location]:
    try:
        return await locations_service.list_locations()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve locations: {str(e)}",
        ) from e
