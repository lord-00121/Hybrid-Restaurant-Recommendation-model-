from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Location(BaseModel):
    area: str = Field(..., description="Neighborhood or area name")
    lat: float = Field(..., description="Latitude coordinate")
    lng: float = Field(..., description="Longitude coordinate")


class RestaurantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    cuisine: List[str] = Field(..., min_length=1, description="List of cuisines offered")
    price_range: str = Field(..., description="Budget, Moderate, Premium, or Fine Dining")
    avg_rating: float = Field(default=3.5, ge=1.0, le=5.0)
    location: Location
    ambience: str = Field(..., description="Casual, Family, Romantic, Trendy, Rooftop, Fine Dining")
    tags: List[str] = Field(default_factory=list, description="Descriptive tags")
    description: str = Field(default="")
    image_url: Optional[str] = Field(default=None)


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    cuisine: Optional[List[str]] = None
    price_range: Optional[str] = None
    avg_rating: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    location: Optional[Location] = None
    ambience: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class RestaurantOut(BaseModel):
    id: str = Field(alias="_id")
    name: str
    cuisine: List[str]
    price_range: str
    avg_rating: float
    location: Location
    ambience: str
    tags: List[str] = Field(default_factory=list)
    description: str = ""
    image_url: Optional[str] = None
    rating_count: Optional[int] = 0
    # Convenience flat field populated in _format_restaurant helpers
    area: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        return str(v) if v is not None else v
