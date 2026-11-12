from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.db_models import Rating, Restaurant
from models.rating import InteractionCreate, InteractionOut, RatingCreate, RatingOut
from routes.auth import get_current_user, get_optional_current_user

router = APIRouter()


def _format_rating(r: Rating) -> dict:
    """Serializes a Rating ORM object to the API response shape."""
    return {
        "id": str(r.id),
        "user_id": str(r.user_id),
        "restaurant_id": str(r.restaurant_id),
        "score": r.score,
        "timestamp": r.timestamp,
    }


def _format_interaction(i) -> dict:
    """Serializes an Interaction ORM object to the API response shape."""
    return {
        "id": str(i.id),
        "user_id": str(i.user_id) if i.user_id is not None else None,
        "restaurant_id": str(i.restaurant_id),
        "interaction_type": i.interaction_type,
        "timestamp": i.timestamp,
    }


@router.post("", response_model=RatingOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def submit_rating(
    rating_in: RatingCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submits or updates a rating (1-5) for a restaurant (requires authentication).

    Recalculates and updates the restaurant's average rating.
    """
    try:
        rest_id = int(rating_in.restaurant_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{rating_in.restaurant_id}' not found",
        )

    # Verify restaurant exists
    result = await db.execute(select(Restaurant).where(Restaurant.id == rest_id))
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{rating_in.restaurant_id}' not found",
        )

    user_id = int(current_user["id"])

    # Upsert the rating
    result = await db.execute(
        select(Rating).where(Rating.user_id == user_id, Rating.restaurant_id == rest_id)
    )
    rating = result.scalar_one_or_none()
    if rating is None:
        rating = Rating(
            user_id=user_id,
            restaurant_id=rest_id,
            score=rating_in.score,
            timestamp=datetime.utcnow(),
        )
        db.add(rating)
    else:
        rating.score = rating_in.score
        rating.timestamp = datetime.utcnow()

    await db.commit()
    await db.refresh(rating)

    # Recalculate average rating and count for this restaurant
    agg = await db.execute(
        select(func.avg(Rating.score), func.count(Rating.id)).where(Rating.restaurant_id == rest_id)
    )
    avg_score, count = agg.one()
    if count:
        restaurant.avg_rating = round(float(avg_score), 2)
        restaurant.rating_count = int(count)
        await db.commit()

    return _format_rating(rating)


@router.get("/me", response_model=List[RatingOut], response_model_by_alias=False)
async def get_my_ratings(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all ratings submitted by the current authenticated user."""
    user_id = int(current_user["id"])
    result = await db.execute(
        select(Rating).where(Rating.user_id == user_id).order_by(Rating.timestamp.desc())
    )
    ratings = result.scalars().all()
    return [_format_rating(r) for r in ratings]


@router.get("/restaurant/{restaurant_id}", response_model=List[RatingOut], response_model_by_alias=False)
async def get_restaurant_ratings(restaurant_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves all ratings submitted for a given restaurant."""
    try:
        rest_id = int(restaurant_id)
    except (TypeError, ValueError):
        return []

    result = await db.execute(
        select(Rating).where(Rating.restaurant_id == rest_id).order_by(Rating.timestamp.desc())
    )
    ratings = result.scalars().all()
    return [_format_rating(r) for r in ratings]


@router.post("/interactions", response_model=InteractionOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def log_interaction(
    interaction_in: InteractionCreate,
    current_user=Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logs an implicit feedback interaction (click, view, etc.)."""
    from models.db_models import Interaction

    try:
        rest_id = int(interaction_in.restaurant_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant with ID '{interaction_in.restaurant_id}' not found",
        )

    interaction = Interaction(
        user_id=int(current_user["id"]) if current_user else None,
        restaurant_id=rest_id,
        interaction_type=interaction_in.interaction_type,
        timestamp=datetime.utcnow(),
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return _format_interaction(interaction)
