from datetime import datetime
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db
from models.rating import InteractionCreate, InteractionOut, RatingCreate, RatingOut
from routes.auth import get_current_user, get_optional_current_user

router = APIRouter()


def _format_doc(doc: dict) -> dict:
    """Helper to convert MongoDB _id to string id."""
    if not doc:
        return {}
    doc["id"] = str(doc["_id"])
    return doc


@router.post("", response_model=RatingOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def submit_rating(
    rating_in: RatingCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Submits or updates a rating (1-5) for a restaurant (requires authentication).

    Recalculates and updates the restaurant's average rating in MongoDB.
    """
    rest_id = str(rating_in.restaurant_id)
    user_id = str(current_user["id"])

    # Verify restaurant exists
    try:
        obj_id = ObjectId(rest_id)
        restaurant = await db.restaurants.find_one({"_id": obj_id})
    except Exception:
        restaurant = await db.restaurants.find_one({"_id": rest_id})

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{rest_id}' not found",
        )

    # Upsert the rating
    filter_q = {"user_id": user_id, "restaurant_id": rest_id}
    now = datetime.utcnow()
    update_doc = {
        "$set": {
            "user_id": user_id,
            "restaurant_id": rest_id,
            "score": rating_in.score,
            "timestamp": now,
        }
    }
    await db.ratings.update_one(filter_q, update_doc, upsert=True)

    # Fetch the saved rating to return
    saved_rating = await db.ratings.find_one(filter_q)

    # Recalculate average rating and count for this restaurant
    all_ratings_cursor = db.ratings.find({"restaurant_id": rest_id})
    all_ratings = await all_ratings_cursor.to_list(length=10000)
    if all_ratings:
        new_avg = round(sum(r["score"] for r in all_ratings) / len(all_ratings), 2)
        rating_count = len(all_ratings)
        try:
            r_query = {"_id": ObjectId(rest_id)}
        except Exception:
            r_query = {"_id": rest_id}

        await db.restaurants.update_one(
            r_query,
            {"$set": {"avg_rating": new_avg, "rating_count": rating_count}},
        )

    return _format_doc(saved_rating)


@router.get("/me", response_model=List[RatingOut], response_model_by_alias=False)
async def get_my_ratings(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Retrieves all ratings submitted by the current authenticated user."""
    user_id = str(current_user["id"])
    cursor = db.ratings.find({"user_id": user_id}).sort("timestamp", -1)
    ratings = await cursor.to_list(length=1000)
    return [_format_doc(r) for r in ratings]


@router.get("/restaurant/{restaurant_id}", response_model=List[RatingOut], response_model_by_alias=False)
async def get_restaurant_ratings(restaurant_id: str, db=Depends(get_db)):
    """Retrieves all ratings submitted for a given restaurant."""
    rest_id = str(restaurant_id)
    cursor = db.ratings.find({"restaurant_id": rest_id}).sort("timestamp", -1)
    ratings = await cursor.to_list(length=1000)
    return [_format_doc(r) for r in ratings]


@router.post("/interactions", response_model=InteractionOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def log_interaction(
    interaction_in: InteractionCreate,
    current_user=Depends(get_optional_current_user),
    db=Depends(get_db),
):
    """Logs an implicit feedback interaction (click, view, etc.)."""
    user_id = str(current_user["id"]) if current_user else None
    rest_id = str(interaction_in.restaurant_id)
    now = datetime.utcnow()

    interaction_doc = {
        "user_id": user_id,
        "restaurant_id": rest_id,
        "interaction_type": interaction_in.interaction_type,
        "timestamp": now,
    }

    result = await db.interactions.insert_one(interaction_doc)
    interaction_doc["_id"] = result.inserted_id
    return _format_doc(interaction_doc)
