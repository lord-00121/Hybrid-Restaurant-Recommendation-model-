from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserPreferences(BaseModel):
    diet: List[str] = Field(default_factory=list, description="Dietary preferences (e.g., Vegetarian, Vegan, Non-Vegetarian)")
    cuisines: List[str] = Field(default_factory=list, description="Preferred cuisines (e.g., North Indian, Italian)")
    ambience: List[str] = Field(default_factory=list, description="Preferred ambiences (e.g., Casual, Romantic, Rooftop)")
    location: str = Field(default="", description="User home city or area")
    budget: str = Field(default="Moderate", description="Preferred budget (Budget, Moderate, Premium, Fine Dining)")

    @field_validator("diet", mode="before")
    @classmethod
    def coerce_diet(cls, v):
        """Accepts a single string or list; 'Any'/empty -> []."""
        if v is None:
            return []
        if isinstance(v, str):
            v = v.strip()
            if not v or v.lower() == "any":
                return []
            if v.lower() == "non-veg":
                return ["Non-Vegetarian"]
            return [v]
        if isinstance(v, (list, tuple)):
            return [str(item).strip() for item in v if str(item).strip() and str(item).strip().lower() != "any"]
        return []

    @field_validator("cuisines", mode="before")
    @classmethod
    def coerce_cuisines(cls, v):
        """Accepts a comma-separated string or list."""
        if v is None:
            return []
        if isinstance(v, str):
            return [c.strip() for c in v.split(",") if c.strip()]
        if isinstance(v, (list, tuple)):
            return [str(item).strip() for item in v if str(item).strip()]
        return []

    @field_validator("ambience", mode="before")
    @classmethod
    def coerce_ambience(cls, v):
        """Accepts a comma-separated string or list."""
        if v is None:
            return []
        if isinstance(v, str):
            return [a.strip() for a in v.split(",") if a.strip()]
        if isinstance(v, (list, tuple)):
            return [str(item).strip() for item in v if str(item).strip()]
        return []

    @field_validator("budget", mode="before")
    @classmethod
    def coerce_budget(cls, v):
        """Maps numeric tier codes to canonical labels."""
        if v is None:
            return "Moderate"
        tier_map = {"1": "Budget", "2": "Moderate", "3": "Premium", "4": "Fine Dining"}
        if isinstance(v, (int, float)):
            return tier_map.get(str(int(v)), "Moderate")
        s = str(v).strip()
        if not s:
            return "Moderate"
        return tier_map.get(s, s)


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    preferences: Optional[UserPreferences] = Field(default_factory=UserPreferences)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: EmailStr
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        return str(v) if v is not None else v


class UserInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    email: EmailStr
    password_hash: str
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        return str(v) if v is not None else v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
