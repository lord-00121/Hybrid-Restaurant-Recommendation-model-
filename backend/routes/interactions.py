from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, status

from database import get_db
from models.rating import InteractionCreate, InteractionOut
from routes.auth import get_optional_current_user

router = APIRouter()


def _format_doc(doc: dict) -> dict:
    """Helper to convert MongoDB _id to string id."""
    if not doc:
        return {}
    doc["id"] = str(doc["_id"])
    return doc


@router.post("", response_model=InteractionOut, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def log_interaction(
    interaction_in: InteractionCreate,
    current_user=Depends(get_optional_current_user),
    db=Depends(get_db),
):
    """Logs an implicit feedback interaction (click, view, bookmark, etc.)."""
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
