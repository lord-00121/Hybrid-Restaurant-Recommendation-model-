from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from database import get_db
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


def _format_restaurant(doc: dict) -> dict:
    """Formats MongoDB restaurant document to match RestaurantOut schema."""
    if not doc:
        return {}
    doc["id"] = str(doc["_id"])
    # Populate convenience flat area field from nested location
    if "location" in doc and isinstance(doc["location"], dict):
        doc["area"] = doc["location"].get("area", "")
    return doc


@router.get("/search", response_model=List[RestaurantOut], response_model_by_alias=False)
async def search_restaurants(
    q: Optional[str] = Query(None, description="General search query for name or cuisine"),
    name: Optional[str] = Query(None, description="Filter by restaurant name (case-insensitive substring)"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine (case-insensitive)"),
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db),
):
    """Searches restaurants by name or cuisine keyword."""
    query_conditions = []

    if q:
        regex_q = {"$regex": q.strip(), "$options": "i"}
        query_conditions.append({
            "$or": [
                {"name": regex_q},
                {"cuisine": regex_q},
                {"tags": regex_q},
                {"location.area": regex_q},
            ]
        })

    if name:
        query_conditions.append({"name": {"$regex": name.strip(), "$options": "i"}})

    if cuisine:
        query_conditions.append({"cuisine": {"$regex": cuisine.strip(), "$options": "i"}})

    mongo_filter = {"$and": query_conditions} if query_conditions else {}

    cursor = db.restaurants.find(mongo_filter).limit(limit)
    restaurants = await cursor.to_list(length=limit)
    return [_format_restaurant(r) for r in restaurants]


@router.get("", response_model=List[RestaurantOut], response_model_by_alias=False)
async def list_restaurants(
    cuisine: Optional[str] = Query(None, description="Filter by cuisine"),
    price_range: Optional[str] = Query(None, description="Filter by price range (Budget, Moderate, Premium, Fine Dining)"),
    ambience: Optional[str] = Query(None, description="Filter by ambience (e.g., Casual, Romantic, Rooftop)"),
    area: Optional[str] = Query(None, description="Filter by area / neighborhood"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db),
):
    """Lists restaurants with optional filtering and pagination."""
    mongo_filter = {}

    cuisines = _split_csv(cuisine)
    if cuisines:
        mongo_filter["cuisine"] = {
            "$in": [{"$regex": f"^{c.strip()}$", "$options": "i"} for c in cuisines]
        }

    price_tiers = _normalize_price_tiers(price_range)
    if price_tiers:
        mongo_filter["price_range"] = {
            "$in": [{"$regex": f"^{t}$", "$options": "i"} for t in price_tiers]
        }

    ambiences = [a.strip() for a in _split_csv(ambience)]
    if ambiences:
        mongo_filter["ambience"] = {
            "$in": [{"$regex": f"^{a}$", "$options": "i"} for a in ambiences]
        }

    if area:
        mongo_filter["location.area"] = {"$regex": area.strip(), "$options": "i"}

    cursor = db.restaurants.find(mongo_filter).skip(skip).limit(limit)
    restaurants = await cursor.to_list(length=limit)
    return [_format_restaurant(r) for r in restaurants]


@router.get("/{restaurant_id}", response_model=RestaurantOut, response_model_by_alias=False)
async def get_restaurant(restaurant_id: str, db=Depends(get_db)):
    """Fetches details of a single restaurant by ID."""
    try:
        obj_id = ObjectId(restaurant_id)
        restaurant = await db.restaurants.find_one({"_id": obj_id})
    except Exception:
        restaurant = await db.restaurants.find_one({"_id": restaurant_id})

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{restaurant_id}' was not found",
        )

    return _format_restaurant(restaurant)


@router.post("", response_model=RestaurantOut, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_in: RestaurantCreate,
    current_admin: dict = Depends(get_current_admin_user),
    db=Depends(get_db),
):
    """Creates a new restaurant entry (admin only)."""
    data = restaurant_in.model_dump()
    result = await db.restaurants.insert_one(data)
    data["_id"] = result.inserted_id
    return _format_restaurant(data)


@router.put("/{restaurant_id}", response_model=RestaurantOut)
async def update_restaurant(
    restaurant_id: str,
    restaurant_update: RestaurantUpdate,
    current_admin: dict = Depends(get_current_admin_user),
    db=Depends(get_db),
):
    """Updates an existing restaurant entry (admin only)."""
    update_data = {k: v for k, v in restaurant_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update",
        )

    try:
        obj_id = ObjectId(restaurant_id)
        query = {"_id": obj_id}
    except Exception:
        query = {"_id": restaurant_id}

    result = await db.restaurants.update_one(query, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{restaurant_id}' not found",
        )

    updated = await db.restaurants.find_one(query)
    return _format_restaurant(updated)


@router.delete("/{restaurant_id}", status_code=status.HTTP_200_OK)
async def delete_restaurant(
    restaurant_id: str,
    current_admin: dict = Depends(get_current_admin_user),
    db=Depends(get_db),
):
    """Deletes a restaurant by ID (admin only)."""
    try:
        obj_id = ObjectId(restaurant_id)
        query = {"_id": obj_id}
    except Exception:
        query = {"_id": restaurant_id}

    result = await db.restaurants.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{restaurant_id}' not found",
        )

    # Clean up associated ratings
    await db.ratings.delete_many({"restaurant_id": restaurant_id})

    return {"status": "success", "message": f"Restaurant {restaurant_id} deleted"}
