from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.db_models import Restaurant
from models.restaurant import RestaurantCreate, RestaurantOut, RestaurantUpdate
from routes.auth import get_current_admin_user

router = APIRouter()

PRICE_TIER_MAP = {
    "1": "budget",
    "2": "moderate",
    "3": "premium",
    "4": "fine dining",
}


def _split_csv(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [v.strip() for v in str(raw).split(",") if v.strip()]


def _normalize_price_tiers(raw: Optional[str]) -> List[str]:
    tiers = []
    for v in _split_csv(raw):
        lv = v.lower()
        tiers.append(PRICE_TIER_MAP.get(lv, lv))
    return tiers


def _restaurant_to_dict(r: Restaurant) -> dict:
    """Serializes a Restaurant ORM object to the dict shape the API expects."""
    loc = r.location or {}
    return {
        "id": str(r.id),
        "name": r.name,
        "cuisine": r.cuisine or [],
        "price_range": r.price_range,
        "avg_rating": r.avg_rating,
        "rating_count": r.rating_count,
        "location": loc,
        "area": loc.get("area", "") if isinstance(loc, dict) else "",
        "ambience": r.ambience,
        "tags": r.tags or [],
        "description": r.description,
        "image_url": r.image_url,
    }


def _matches_restaurant_filters(
    r: Restaurant,
    *,
    cuisines: List[str],
    price_tiers: List[str],
    ambiences: List[str],
    area: Optional[str],
) -> bool:
    """Python-side filter for JSON-list fields (cuisine/tags) — dialect agnostic."""
    if price_tiers:
        if str(r.price_range or "").strip().lower() not in price_tiers:
            return False

    if cuisines:
        rest_cuisines = r.cuisine or []
        if isinstance(rest_cuisines, str):
            rest_cuisines = [rest_cuisines]
        rest_cuisines_lower = [str(c).strip().lower() for c in rest_cuisines]
        if not any(t in rc for t in cuisines for rc in rest_cuisines_lower):
            return False

    if ambiences:
        if str(r.ambience or "").strip().lower() not in ambiences:
            return False

    if area:
        loc = r.location or {}
        area_val = str(loc.get("area", "") if isinstance(loc, dict) else "").lower()
        if area.strip().lower() not in area_val:
            return False

    return True


@router.get("/search", response_model=List[RestaurantOut], response_model_by_alias=False)
async def search_restaurants(
    q: Optional[str] = Query(None, description="General search query for name or cuisine"),
    name: Optional[str] = Query(None, description="Filter by restaurant name (case-insensitive substring)"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine (case-insensitive)"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Searches restaurants by name or cuisine keyword."""
    stmt = select(Restaurant)

    if name:
        stmt = stmt.where(Restaurant.name.ilike(f"%{name.strip()}%"))

    result = await db.execute(stmt)
    restaurants = result.scalars().all()

    q_lower = q.strip().lower() if q else None
    cuisine_lower = cuisine.strip().lower() if cuisine else None

    filtered = []
    for r in restaurants:
        if q_lower:
            haystacks = [r.name or ""]
            haystacks.extend(str(c) for c in (r.cuisine or []))
            haystacks.extend(str(t) for t in (r.tags or []))
            loc = r.location or {}
            haystacks.append(str(loc.get("area", "") if isinstance(loc, dict) else ""))
            if not any(q_lower in h.lower() for h in haystacks):
                continue
        if cuisine_lower:
            rest_cuisines = [str(c).lower() for c in (r.cuisine or [])]
            if not any(cuisine_lower in c for c in rest_cuisines):
                continue
        filtered.append(r)

    return [_restaurant_to_dict(r) for r in filtered[:limit]]


@router.get("", response_model=List[RestaurantOut], response_model_by_alias=False)
async def list_restaurants(
    cuisine: Optional[str] = Query(None, description="Filter by cuisine"),
    price_range: Optional[str] = Query(None, description="Filter by price range (Budget, Moderate, Premium, Fine Dining)"),
    ambience: Optional[str] = Query(None, description="Filter by ambience (e.g., Casual, Romantic, Rooftop)"),
    area: Optional[str] = Query(None, description="Filter by area / neighborhood"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Lists restaurants with optional filtering and pagination."""
    stmt = select(Restaurant).order_by(Restaurant.id)
    result = await db.execute(stmt)
    restaurants = result.scalars().all()

    cuisines = [c.lower() for c in _split_csv(cuisine)]
    price_tiers = _normalize_price_tiers(price_range)
    ambiences = [a.lower() for a in _split_csv(ambience)]

    filtered = [
        r for r in restaurants
        if _matches_restaurant_filters(
            r,
            cuisines=cuisines,
            price_tiers=price_tiers,
            ambiences=ambiences,
            area=area,
        )
    ]

    page = filtered[skip:skip + limit]
    return [_restaurant_to_dict(r) for r in page]


@router.get("/{restaurant_id}", response_model=RestaurantOut, response_model_by_alias=False)
async def get_restaurant(restaurant_id: str, db: AsyncSession = Depends(get_db)):
    """Fetches details of a single restaurant by ID."""
    try:
        rid = int(restaurant_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{restaurant_id}' was not found",
        )

    result = await db.execute(select(Restaurant).where(Restaurant.id == rid))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{restaurant_id}' was not found",
        )

    return _restaurant_to_dict(restaurant)


@router.post("", response_model=RestaurantOut, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_in: RestaurantCreate,
    current_admin: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new restaurant entry (admin only)."""
    data = restaurant_in.model_dump()
    new_rest = Restaurant(**data)
    db.add(new_rest)
    await db.commit()
    await db.refresh(new_rest)
    return _restaurant_to_dict(new_rest)


@router.put("/{restaurant_id}", response_model=RestaurantOut)
async def update_restaurant(
    restaurant_id: str,
    restaurant_update: RestaurantUpdate,
    current_admin: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates an existing restaurant entry (admin only)."""
    try:
        rid = int(restaurant_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{restaurant_id}' not found",
        )

    result = await db.execute(select(Restaurant).where(Restaurant.id == rid))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{restaurant_id}' not found",
        )

    update_data = {k: v for k, v in restaurant_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update",
        )

    for field, value in update_data.items():
        setattr(restaurant, field, value)

    await db.commit()
    await db.refresh(restaurant)
    return _restaurant_to_dict(restaurant)


@router.delete("/{restaurant_id}", status_code=status.HTTP_200_OK)
async def delete_restaurant(
    restaurant_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a restaurant by ID (admin only)."""
    try:
        rid = int(restaurant_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{restaurant_id}' not found",
        )

    result = await db.execute(select(Restaurant).where(Restaurant.id == rid))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{restaurant_id}' not found",
        )

    await db.delete(restaurant)
    await db.commit()

    return {"status": "success", "message": f"Restaurant {restaurant_id} deleted"}
