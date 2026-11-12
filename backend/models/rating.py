from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RatingCreate(BaseModel):
    restaurant_id: str
    score: int = Field(..., ge=1, le=5, description="Rating score from 1 to 5")


class RatingOut(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    restaurant_id: str
    score: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        return str(v) if v is not None else v


class InteractionCreate(BaseModel):
    restaurant_id: str
    interaction_type: str = Field(..., description="Interaction type such as 'click', 'view', or 'bookmark'")


class InteractionOut(BaseModel):
    id: str = Field(alias="_id")
    user_id: Optional[str] = None
    restaurant_id: str
    interaction_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        return str(v) if v is not None else v
