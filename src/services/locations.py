"""Location information service."""

from typing import Annotated

from fastapi import Depends

from ..models.location import Category, Location


class LocationsService:
    """Service for location information operations."""

    async def list_locations(self) -> list[Location]:
        """List all locations (mock implementation)."""
        # Example categories
        category1 = Category(id="1", name="Restaurant")
        category2 = Category(id="2", name="Lounge")
        category3 = Category(id="3", name="Saloon")
        category4 = Category(id="4", name="Fashion Store")

        # Example locations
        location1 = Location(
            id="loc1",
            name="Skyview Restaurant",
            description="A rooftop restaurant with a great view.",
            address="Terminal 1, Level 3",
            state="Telangana",
            opening_time="08:00",
            closing_time="23:00",
            website_links=["https://skyview.example.com"],
            categories=[category1],
            tags=["food", "view"],
            floor="3"
        )
        location2 = Location(
            id="loc2",
            name="Executive Lounge",
            description="Premium lounge for business travelers.",
            address="Terminal 2, Level 2",
            state="Telangana",
            opening_time="06:00",
            closing_time="22:00",
            website_links=["https://lounge.example.com"],
            categories=[category2],
            tags=["lounge", "business", "food"],
            floor="2"
        )
        location3 = Location(
            id="loc3",
            name="KFC",
            description="Popular fast-food chain serving fried chicken, burgers, and more.",
            address="Terminal 1, Food Court",
            state="Telangana",
            opening_time="10:00",
            closing_time="23:00",
            website_links=["https://www.kfc.co.in/"],
            categories=[category1],
            tags=["fast-food", "chicken", "restaurant", "family", "broasted chicken"],
            floor="1"
        )
        location4 = Location(
            id="loc4",
            name="Subway",
            description="International sandwich chain offering fresh subs and salads.",
            address="Terminal 1, Food Court",
            state="Telangana",
            opening_time="09:00",
            closing_time="22:00",
            website_links=["https://www.subway.com/"],
            categories=[category1],
            tags=["fast-food", "sandwich", "healthy", "restaurant"],
            floor="1"
        )
        location5 = Location(
            id="loc5",
            name="Elite Saloon",
            description="Professional saloon offering haircuts, styling, and grooming services.",
            address="Terminal 2, Level 1",
            state="Telangana",
            opening_time="08:00",
            closing_time="21:00",
            website_links=["https://elitesaloon.example.com"],
            categories=[category3],
            tags=["saloon", "grooming", "haircut", "beauty"],
            floor="1"
        )
        location6 = Location(
            id="loc6",
            name="Trendy Threads",
            description="Fashion store featuring the latest trends in clothing and accessories.",
            address="Terminal 1, Level 2",
            state="Telangana",
            opening_time="10:00",
            closing_time="22:00",
            website_links=["https://trendythreads.example.com"],
            categories=[category4],
            tags=["fashion", "clothing", "accessories", "store"],
            floor="2"
        )
        location7 = Location(
            id="loc7",
            name="Urban Vogue",
            description="Premium fashion boutique with exclusive designer wear.",
            address="Terminal 2, Level 3",
            state="Telangana",
            opening_time="11:00",
            closing_time="21:00",
            website_links=["https://urbanvogue.example.com"],
            categories=[category4],
            tags=["fashion", "designer", "boutique", "clothing"],
            floor="3"
        )
        return [
            location1,
            location2,
            location3,
            location4,
            location5,
            location6,
            location7,
        ]

def get_locations_service() -> LocationsService:
    """Dependency to get locations service instance."""
    return LocationsService()

# Type alias for dependency injection
LocationsServiceDep = Annotated[LocationsService, Depends(get_locations_service)]
