import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from fastapi import APIRouter, Depends, Query

from database import get_db
from engine.collaborative import CollaborativeEngine
from engine.content_based import ContentBasedEngine
from engine.hybrid import HybridEngine
from engine.preprocess import build_restaurant_feature_matrix, build_user_profile, build_preference_profile
from routes.auth import get_optional_current_user

router = APIRouter()

# Instantiate singletons for recommendation engines
content_engine = ContentBasedEngine()
collab_engine = CollaborativeEngine()
hybrid_engine = HybridEngine()

# Reference coordinates for major Indian cities for geographic filtering
CITY_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "delhi": (28.6139, 77.2090),
    "new delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "pune": (18.5204, 73.8567),
    "kolkata": (22.5726, 88.3639),
}

# Maps numeric price tier codes (used by the frontend) to canonical labels
PRICE_TIER_MAP = {
    "1": "budget",
    "2": "moderate",
    "3": "premium",
    "4": "fine dining",
}


def _split_csv(raw: Optional[str]) -> List[str]:
    """Splits a comma-separated query param into a list of stripped values."""
    if not raw:
        return []
    return [v.strip() for v in str(raw).split(",") if v.strip()]


def _normalize_price_tiers(raw: Optional[str]) -> List[str]:
    """Normalizes price_range query values to lowercase canonical labels."""
    tiers = []
    for v in _split_csv(raw):
        lv = v.lower()
        tiers.append(PRICE_TIER_MAP.get(lv, lv))
    return tiers


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _format_restaurant(doc: dict) -> dict:
    """Formats a MongoDB restaurant document to string IDs."""
    d = dict(doc)
    d["id"] = str(d["_id"])
    d["_id"] = str(d["_id"])
    # Populate convenience flat area field from nested location
    if "location" in d and isinstance(d["location"], dict):
        d["area"] = d["location"].get("area", "")
    return d


@router.get("")
async def get_recommendations(
    top_n: int = Query(10, ge=1, le=250, description="Number of recommendations to return"),
    price_range: Optional[str] = Query(None, description="Filter by price range (Budget, Moderate, Premium, Fine Dining)"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine (e.g., North Indian, Italian)"),
    ambience: Optional[str] = Query(None, description="Filter by ambience (e.g., Casual, Romantic, Rooftop)"),
    max_distance_km: Optional[float] = Query(50.0, ge=0.5, le=5000.0, description="Max distance in km"),
    user_lat: Optional[float] = Query(None, description="User latitude coordinate"),
    user_lng: Optional[float] = Query(None, description="User longitude coordinate"),
    alpha: Optional[float] = Query(None, ge=0.0, le=1.0, description="Optional manual override for alpha weight"),
    current_user=Depends(get_optional_current_user),
    db=Depends(get_db),
):
    """Generates personalized hybrid recommendations for the user.

    - Content-based: Cosine similarity on restaurant features and user profile
    - Collaborative: Pearson correlation with top-20 similar users (TruncatedSVD fallback)
    - Dynamic cold-start alpha tuning based on user rating count
    - Unauthenticated users receive top popular restaurants sorted by rating
    """
    # 1. Fetch all restaurants from DB
    restaurants_cursor = db.restaurants.find({})
    raw_restaurants = await restaurants_cursor.to_list(length=2000)

    if not raw_restaurants:
        return {
            "recommendations": [],
            "alpha_used": None,
            "user_rating_count": 0,
            "total_candidates": 0,
        }

    # Determine reference coordinates for distance filtering
    ref_lat = user_lat
    ref_lng = user_lng

    if ref_lat is None or ref_lng is None:
        if current_user and current_user.get("preferences", {}).get("location"):
            user_loc = str(current_user["preferences"]["location"]).strip().lower()
            for city_name, coords in CITY_CENTROIDS.items():
                if city_name in user_loc:
                    ref_lat, ref_lng = coords
                    break

    # Helper filter function
    def matches_filters(rest: dict) -> Tuple[bool, Optional[float]]:
        # Filter: Price Range (supports comma-separated list + numeric tiers)
        allowed_prices = _normalize_price_tiers(price_range)
        if allowed_prices:
            rest_price = str(rest.get("price_range", "")).strip().lower()
            if rest_price not in allowed_prices:
                return False, None

        # Filter: Cuisine (supports comma-separated list, substring match)
        target_cuisines = [c.lower() for c in _split_csv(cuisine)]
        if target_cuisines:
            rest_cuisines = rest.get("cuisine", [])
            if isinstance(rest_cuisines, str):
                rest_cuisines = [rest_cuisines]
            rest_cuisines_lower = [str(c).strip().lower() for c in rest_cuisines]
            if not any(
                target in rc
                for target in target_cuisines
                for rc in rest_cuisines_lower
            ):
                return False, None

        # Filter: Ambience (supports comma-separated list, case-insensitive)
        target_ambiences = [a.lower() for a in _split_csv(ambience)]
        if target_ambiences:
            rest_ambience = str(rest.get("ambience", "")).strip().lower()
            if rest_ambience not in target_ambiences:
                return False, None

        # Filter: Geographic Distance
        dist_km = None
        if ref_lat is not None and ref_lng is not None:
            loc = rest.get("location", {})
            r_lat = loc.get("lat")
            r_lng = loc.get("lng")
            if r_lat is not None and r_lng is not None:
                dist_km = round(haversine_distance(ref_lat, ref_lng, float(r_lat), float(r_lng)), 2)
                if max_distance_km is not None and dist_km > max_distance_km:
                    return False, dist_km

        return True, dist_km

    # CASE A: Unauthenticated guest user -> Return popular restaurants
    if not current_user:
        filtered_popular = []
        for r in raw_restaurants:
            passed, dist_km = matches_filters(r)
            if passed:
                item = _format_restaurant(r)
                item["hybrid_score"] = None
                item["content_score"] = None
                item["collab_score"] = None
                item["reason"] = "Popular choice with high diner ratings"
                item["distance_km"] = dist_km
                filtered_popular.append(item)

        filtered_popular.sort(key=lambda x: float(x.get("avg_rating", 0.0)), reverse=True)
        top_popular = filtered_popular[:top_n]

        return {
            "recommendations": top_popular,
            "alpha_used": None,
            "user_rating_count": 0,
            "total_candidates": len(filtered_popular),
        }

    # CASE B: Authenticated user -> Compute Hybrid Recommendations
    user_id = str(current_user["id"])

    # Fetch all ratings
    ratings_cursor = db.ratings.find({})
    raw_ratings = await ratings_cursor.to_list(length=20000)

    # 1. Feature matrix and user profile
    feature_matrix, rest_ids = build_restaurant_feature_matrix(raw_restaurants)
    user_profile = build_user_profile(user_id, raw_ratings, feature_matrix, rest_ids)

    # 2. Count user's ratings for dynamic alpha calculation
    user_ratings = [r for r in raw_ratings if str(r.get("user_id")) == user_id]
    user_rating_count = len(user_ratings)

    # 2b. Cold-start handling: blend in a preference-based profile synthesized
    # from the user's onboarding questionnaire answers (cuisines, budget,
    # ambience, diet). Weight shifts from preferences toward ratings as the
    # user accumulates rating history.
    user_prefs = current_user.get("preferences", {}) if current_user else {}
    pref_profile = build_preference_profile(user_prefs, feature_matrix)
    if pref_profile.size > 0 and np.linalg.norm(pref_profile) > 0:
        if user_rating_count == 0:
            user_profile = pref_profile
        elif user_rating_count < 5:
            # Linear blend: preferences dominate early, ratings take over
            rating_weight = user_rating_count / 5.0
            pref_weight = 1.0 - rating_weight
            rating_norm = user_profile / (np.linalg.norm(user_profile) + 1e-9) if np.linalg.norm(user_profile) > 0 else user_profile
            user_profile = rating_weight * rating_norm + pref_weight * pref_profile

    # Determine alpha
    if alpha is not None:
        effective_alpha = float(alpha)
    else:
        effective_alpha = hybrid_engine.get_alpha(user_rating_count)

    # 3. Compute Content-Based Scores
    content_scores = content_engine.compute_scores(user_profile, feature_matrix)

    # 4. Compute Collaborative Filtering Scores
    rating_matrix = collab_engine.build_rating_matrix(raw_ratings)
    collab_scores = collab_engine.compute_scores(user_id, rating_matrix)

    # 5. Compute Hybrid Scores
    visited_ids = {str(r.get("restaurant_id")) for r in user_ratings}
    scored_items = hybrid_engine.compute_hybrid_scores(
        content_scores=content_scores,
        collab_scores=collab_scores,
        alpha=effective_alpha,
        visited_ids=visited_ids,
        all_restaurant_ids=rest_ids,
    )

    # 6. Apply filters and merge full restaurant details
    rest_map = {str(r["_id"]): r for r in raw_restaurants}
    final_recommendations = []

    for scored in scored_items:
        rest_id = scored["restaurant_id"]
        restaurant_doc = rest_map.get(rest_id)
        if not restaurant_doc:
            continue

        passed, dist_km = matches_filters(restaurant_doc)
        if not passed:
            continue

        item = _format_restaurant(restaurant_doc)
        item["hybrid_score"] = scored["hybrid_score"]
        item["content_score"] = scored["content_score"]
        item["collab_score"] = scored["collab_score"]
        item["reason"] = scored["reason"]
        item["distance_km"] = dist_km
        final_recommendations.append(item)

    top_recommendations = hybrid_engine.get_top_n(final_recommendations, top_n)

    return {
        "recommendations": top_recommendations,
        "alpha_used": effective_alpha,
        "user_rating_count": user_rating_count,
        "total_candidates": len(final_recommendations),
    }
