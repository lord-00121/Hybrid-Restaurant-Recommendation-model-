from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.db_models import Interaction, Rating, Restaurant, User

router = APIRouter()


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Returns aggregated platform statistics for the admin dashboard."""
    total_restaurants = (await db.execute(select(func.count(Restaurant.id)))).scalar() or 0
    total_ratings = (await db.execute(select(func.count(Rating.id)))).scalar() or 0
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_interactions = (await db.execute(select(func.count(Interaction.id)))).scalar() or 0

    return {
        "total_restaurants": total_restaurants,
        "total_ratings": total_ratings,
        "total_users": total_users,
        "total_interactions": total_interactions,
    }
