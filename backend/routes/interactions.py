from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.db_models import Interaction, Restaurant
from models.rating import InteractionCreate, InteractionOut
from routes.auth import get_optional_current_user

router = APIRouter()


@router.post("", response_model=InteractionOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def log_interaction(
    interaction_in: InteractionCreate,
    current_user=Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logs an implicit feedback interaction (click, view, bookmark, etc.)."""
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

    return {
        "id": str(interaction.id),
        "user_id": str(interaction.user_id) if interaction.user_id is not None else None,
        "restaurant_id": str(interaction.restaurant_id),
        "interaction_type": interaction.interaction_type,
        "timestamp": interaction.timestamp,
    }
