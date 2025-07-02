from typing import Optional

from pydantic import BaseModel, HttpUrl

from .category import Category


class Location(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    website_links: Optional[list[HttpUrl]] = []
    categories: Optional[list[Category]] = []
    tags: Optional[list[str]] = []
    floor: Optional[str] = None
