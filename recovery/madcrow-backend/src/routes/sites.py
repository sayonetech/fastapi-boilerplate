"""Site information routes."""

from fastapi import APIRouter, HTTPException

from ..mcp.descriptions import SITE_GET_INFO_DESCRIPTION
from ..models.sites import SiteInfo
from ..services.sites import SitesServiceDep

sites_router = APIRouter()


@sites_router.get(
    "/get-info",
    operation_id="get_site_info",
    response_model=SiteInfo,
    description=SITE_GET_INFO_DESCRIPTION,
)
async def get_site_info(
    sites_service: SitesServiceDep,
) -> SiteInfo:
    try:
        return await sites_service.get_site_info()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve site information: {str(e)}",
        ) from e
