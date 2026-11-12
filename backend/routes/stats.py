from fastapi import APIRouter, Depends
from database import get_db

router = APIRouter()


@router.get("")
async def get_stats(db=Depends(get_db)):
    """Returns aggregated platform statistics for the admin dashboard."""
    total_restaurants = await db.restaurants.count_documents({})
    total_ratings = await db.ratings.count_documents({})
    total_users = await db.users.count_documents({})
    total_interactions = await db.interactions.count_documents({})

    return {
        "total_restaurants": total_restaurants,
        "total_ratings": total_ratings,
        "total_users": total_users,
        "total_interactions": total_interactions,
    }
