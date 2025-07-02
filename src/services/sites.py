"""Site information service."""

from typing import Annotated

from fastapi import Depends
from pydantic import HttpUrl

from ..models.sites import OperationHours, SiteInfo


class SitesService:
    """Service for site information operations."""

    async def get_site_info(self) -> SiteInfo:
        """Get information for the site."""
        # This is a mock implementation - replace with actual data source
        # (database, external API, etc.)

        # Example site data based on the provided structure
        example_site = SiteInfo(
            siteId="67dcf5dd2f21c64e3225254f",
            mapId="aa71c9f8df2d5e76b12dc6a2106d6d0b",
            siteName="Rajiv Gandhi International Airport",
            operationHours=[
                OperationHours(
                    opens="00:00",
                    closes="23:59",
                    dayOfWeek=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                )
            ],
            latitude=17.23559065,
            longitude=78.4294370585205,
            address=(
                "Rajiv Gandhi International Airport, Departure Dr, "
                "Balapur mandal, Ranga Reddy, Telangana, 500006, India"
            ),
            city="Hyderabad",
            countryCode="IN",
            postal="500006",
            state="Telangana",
            telephone="914066546370",
            topLocations=[],
            tzId="Asia/Calcutta",
            utcOffset="+5:30",
            link=HttpUrl("https://www.hyderabad.aero/"),
            type="AIRPORT",
        )
        return example_site


def get_sites_service() -> SitesService:
    """Dependency to get sites service instance."""
    return SitesService()


# Type alias for dependency injection
SitesServiceDep = Annotated[SitesService, Depends(get_sites_service)]
