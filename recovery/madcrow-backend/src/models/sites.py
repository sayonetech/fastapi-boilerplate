"""
Site information models for the Beco ecosystem.

A Site is the core entity in the Beco ecosystem, representing a venue such as a mall, airport, university, or office.
"""

from pydantic import BaseModel, Field, HttpUrl


class OperationHours(BaseModel):
    """Operation hours model for a site."""

    opens: str = Field(..., description="Opening time in HH:MM format")
    closes: str = Field(..., description="Closing time in HH:MM format")
    dayOfWeek: list[str] = Field(..., description="List of days of the week")


class TopLocation(BaseModel):
    """Top location model for a site."""

    # This is a placeholder - you can extend this based on your needs


class SiteInfo(BaseModel):
    """
    Site information response model.

    A Site is a core venue in the Beco ecosystem. It can represent a mall, airport,
    university, office, or similar large venue.
    """

    siteId: str = Field(..., description="Unique identifier for the site")
    mapId: str = Field(..., description="Map identifier for the site")
    siteName: str = Field(..., description="Name of the site")
    operationHours: list[OperationHours] = Field(..., description="Operating hours for the site")
    latitude: float = Field(..., description="Latitude coordinate of the site")
    longitude: float = Field(..., description="Longitude coordinate of the site")
    address: str = Field(..., description="Full address of the site")
    city: str | None = Field(None, description="City where the site is located")
    countryCode: str | None = Field(None, description="Country code")
    postal: str | None = Field(None, description="Postal code")
    state: str | None = Field(None, description="State or province")
    telephone: str = Field(..., description="Contact telephone number")
    topLocations: list[TopLocation] = Field(default_factory=list, description="Top locations within the site")
    tzId: str = Field(..., description="Time zone identifier")
    utcOffset: str = Field(..., description="UTC offset")
    link: HttpUrl = Field(..., description="Website link for the site")
    type: str = Field(..., description="Type of the site (e.g., MALL, AIRPORT, UNIVERSITY, OFFICE)")
