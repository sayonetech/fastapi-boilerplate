"""Site-related MCP tools."""

from fastapi import HTTPException

from src.extensions.ext_mcp import mcp_wrapper
from src.models.sites import SiteInfo
from src.services.sites import SitesService

from ..descriptions import SITE_GET_INFO_DESCRIPTION

mcp = mcp_wrapper


@mcp.tool(
    name="get_site_info",  # Custom tool name for the LLM
    description=SITE_GET_INFO_DESCRIPTION,  # Custom description
    tags={"get-site", "venue-details"},  # Optional tags for organization/filtering
)
async def get_site_info() -> SiteInfo:
    """
    Get comprehensive information about the current site.
    Returns detailed information about the site including:
    - Site ID and map ID
    - Site name and type
    - Operating hours
    - Location coordinates (latitude/longitude)
    - Address and contact information
    - Timezone information
    - Website link
    This tool is useful for getting context about the current venue when providing
    location-based services or navigation assistance.
    """
    try:
        sites_service = SitesService()
        return await sites_service.get_site_info()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve site information: {str(e)}",
        ) from e
