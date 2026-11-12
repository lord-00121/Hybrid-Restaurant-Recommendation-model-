from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd


def build_restaurant_feature_matrix(
    restaurants: List[Dict[str, Any]]
) -> Tuple[pd.DataFrame, List[str]]:
    """Builds a normalized feature matrix for all restaurants.

    One-hot encodes cuisine, price_range, ambience, and tags.
    Normalizes avg_rating to the [0, 1] range.

    Returns:
        (pd.DataFrame indexed by restaurant_id, list of restaurant_ids)
    """
    if not restaurants:
        return pd.DataFrame(), []

    restaurant_ids: List[str] = []
    rows: List[Dict[str, float]] = []

    # Collect vocabulary of unique categorical values
    all_cuisines = set()
    all_prices = set()
    all_ambiences = set()
    all_tags = set()

    for r in restaurants:
        cuisines = r.get("cuisine", [])
        if isinstance(cuisines, str):
            cuisines = [c.strip() for c in cuisines.split(",")]
        for c in cuisines:
            if c:
                all_cuisines.add(c.strip())

        price = r.get("price_range")
        if price:
            all_prices.add(str(price).strip())

        amb = r.get("ambience")
        if amb:
            all_ambiences.add(str(amb).strip())

        tags = r.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        for t in tags:
            if t:
                all_tags.add(t.strip())

    sorted_cuisines = sorted(all_cuisines)
    sorted_prices = sorted(all_prices)
    sorted_ambiences = sorted(all_ambiences)
    sorted_tags = sorted(all_tags)

    for r in restaurants:
        rest_id = str(r.get("_id") or r.get("id"))
        restaurant_ids.append(rest_id)

        feat: Dict[str, float] = {}

        # 1. One-hot encode cuisine
        rest_cuisines = r.get("cuisine", [])
        if isinstance(rest_cuisines, str):
            rest_cuisines = [c.strip() for c in rest_cuisines.split(",")]
        rest_cuisines_set = {c.strip() for c in rest_cuisines}
        for c in sorted_cuisines:
            feat[f"cuisine_{c}"] = 1.0 if c in rest_cuisines_set else 0.0

        # 2. One-hot encode price_range
        rest_price = str(r.get("price_range", "")).strip()
        for p in sorted_prices:
            feat[f"price_{p}"] = 1.0 if p == rest_price else 0.0

        # 3. One-hot encode ambience
        rest_amb = str(r.get("ambience", "")).strip()
        for a in sorted_ambiences:
            feat[f"ambience_{a}"] = 1.0 if a == rest_amb else 0.0

        # 4. One-hot encode tags
        rest_tags = r.get("tags", [])
        if isinstance(rest_tags, str):
            rest_tags = [t.strip() for t in rest_tags.split(",")]
        rest_tags_set = {t.strip() for t in rest_tags}
        for t in sorted_tags:
            feat[f"tag_{t}"] = 1.0 if t in rest_tags_set else 0.0

        # 5. Normalize avg_rating to [0, 1] (standard scale 1.0 to 5.0)
        raw_rating = float(r.get("avg_rating", 3.0))
        norm_rating = (raw_rating - 1.0) / 4.0
        feat["avg_rating_norm"] = float(np.clip(norm_rating, 0.0, 1.0))

        rows.append(feat)

    df = pd.DataFrame(rows, index=restaurant_ids)
    return df, restaurant_ids


def build_user_profile(
    user_id: str,
    ratings: List[Dict[str, Any]],
    feature_matrix: pd.DataFrame,
    restaurant_ids: List[str],
) -> np.ndarray:
    """Builds a user taste profile vector from rated restaurants.

    Calculates a weighted average of feature vectors for restaurants rated >= 3.
    If no ratings are >= 3, falls back to using all ratings for that user.
    If the user has no ratings at all, returns a zero vector.

    Returns:
        1D numpy array representing the user profile.
    """
    if feature_matrix.empty or not restaurant_ids:
        return np.zeros(feature_matrix.shape[1] if not feature_matrix.empty else 0, dtype=np.float64)

    target_uid = str(user_id)
    user_ratings = [
        r for r in ratings
        if str(r.get("user_id")) == target_uid and str(r.get("restaurant_id")) in feature_matrix.index
    ]

    if not user_ratings:
        return np.zeros(feature_matrix.shape[1], dtype=np.float64)

    # Use high ratings (>= 3.0) if present, else fallback to all ratings
    high_ratings = [r for r in user_ratings if float(r.get("score", 0)) >= 3.0]
    selected_ratings = high_ratings if high_ratings else user_ratings

    weighted_sum = np.zeros(feature_matrix.shape[1], dtype=np.float64)
    total_weight = 0.0

    for r in selected_ratings:
        score = float(r.get("score", 3.0))
        rest_id = str(r.get("restaurant_id"))
        feat_vector = feature_matrix.loc[rest_id].values.astype(np.float64)
        weighted_sum += score * feat_vector
        total_weight += score

    if total_weight > 0.0:
        return weighted_sum / total_weight
    return np.zeros(feature_matrix.shape[1], dtype=np.float64)


def build_preference_profile(
    preferences: Dict[str, Any],
    feature_matrix: pd.DataFrame,
) -> np.ndarray:
    """Builds a synthetic user taste profile from stated onboarding preferences.

    Used for cold-start users who have few or no ratings. Maps preferred
    cuisines, budget tier, and ambiences onto the one-hot feature columns
    of the restaurant feature matrix.

    Returns:
        1D numpy array of the same width as feature_matrix columns.
    """
    if feature_matrix.empty:
        return np.zeros(0, dtype=np.float64)

    profile = np.zeros(feature_matrix.shape[1], dtype=np.float64)
    cols = feature_matrix.columns

    prefs = preferences or {}

    # 1. Preferred cuisines -> cuisine_* columns
    cuisines = prefs.get("cuisines", [])
    if isinstance(cuisines, str):
        cuisines = [c.strip() for c in cuisines.split(",") if c.strip()]
    for c in cuisines:
        col = f"cuisine_{str(c).strip()}"
        if col in cols:
            profile[cols.get_loc(col)] = 1.0

    # 2. Budget tier -> price_* column
    budget = str(prefs.get("budget", "")).strip()
    if budget:
        col = f"price_{budget}"
        if col in cols:
            profile[cols.get_loc(col)] = 1.0

    # 3. Preferred ambiences -> ambience_* columns
    ambiences = prefs.get("ambience", [])
    if isinstance(ambiences, str):
        ambiences = [a.strip() for a in ambiences.split(",") if a.strip()]
    for a in ambiences:
        col = f"ambience_{str(a).strip()}"
        if col in cols:
            profile[cols.get_loc(col)] = 1.0

    # 4. Dietary preference -> boost vegetarian-friendly tags if present
    diet = prefs.get("diet", [])
    if isinstance(diet, str):
        diet = [diet]
    diet_lower = [str(d).lower() for d in diet]
    if any("veg" in d and "non" not in d for d in diet_lower):
        for tag_col in cols:
            if tag_col.startswith("tag_") and "veg" in tag_col.lower():
                profile[cols.get_loc(tag_col)] = max(profile[cols.get_loc(tag_col)], 0.6)

    # Normalize to unit length for stable cosine similarity
    norm = np.linalg.norm(profile)
    if norm > 0:
        profile = profile / norm
    return profile


def normalize_scores(scores: np.ndarray) -> np.ndarray:
    """Min-max normalizes scores to the [0, 1] range.

    If all values are identical or input is empty, returns safe values.
    """
    arr = np.asarray(scores, dtype=np.float64)
    if arr.size == 0:
        return arr

    min_val = np.min(arr)
    max_val = np.max(arr)

    if max_val - min_val > 1e-9:
        return (arr - min_val) / (max_val - min_val)
    return np.full_like(arr, 0.5)
