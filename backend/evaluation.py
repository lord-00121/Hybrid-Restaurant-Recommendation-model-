"""
Offline Evaluation / Benchmarking Module
=========================================
Evaluates the hybrid restaurant recommendation system with industry-standard
information-retrieval and rating-prediction metrics.

Metrics
-------
- Precision@K : fraction of recommended items that are relevant
- Recall@K    : fraction of relevant items that appear in recommendations
- NDCG@K      : normalised discounted cumulative gain
- RMSE        : root mean square error (predicted vs actual rating)
- MAE         : mean absolute error (predicted vs actual rating)
- Coverage    : fraction of the restaurant catalogue recommended across users

Usage
-----
    python evaluation.py          # standalone CLI
    GET /api/evaluation           # FastAPI route (see routes/evaluation.py)
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Path setup – make sure `engine.*` and `database` are importable when this
# module is executed as a standalone script.
# ---------------------------------------------------------------------------
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database import get_sync_db
from engine.collaborative import CollaborativeEngine
from engine.content_based import ContentBasedEngine
from engine.hybrid import HybridEngine
from engine.preprocess import (
    build_restaurant_feature_matrix,
    build_user_profile,
    normalize_scores,
)

# ── engine singletons ──────────────────────────────────────────────────────
content_engine = ContentBasedEngine()
collab_engine = CollaborativeEngine()
hybrid_engine = HybridEngine()

# ── strategy configurations ────────────────────────────────────────────────
STRATEGIES: Dict[str, float] = {
    "content_only": 1.0,       # pure content-based
    "collaborative_only": 0.0,  # pure collaborative filtering
    "hybrid": 0.5,              # balanced blend
}

RELEVANCE_THRESHOLD = 4.0  # rating >= this counts as "relevant"


# ═══════════════════════════════════════════════════════════════════════════
#  Metric helpers
# ═══════════════════════════════════════════════════════════════════════════

def precision_at_k(recommended_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """Fraction of the top-K recommendations that are relevant."""
    if k <= 0:
        return 0.0
    top_k = recommended_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(top_k)


def recall_at_k(recommended_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """Fraction of relevant items that appear in the top-K recommendations."""
    if not relevant_ids or k <= 0:
        return 0.0
    top_k = recommended_ids[:k]
    hits = sum(1 for rid in top_k if rid in relevant_ids)
    return hits / len(relevant_ids)


def ndcg_at_k(recommended_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """Normalised Discounted Cumulative Gain at K.

    Relevance is binary: 1 if the item is in ``relevant_ids``, else 0.
    """
    if k <= 0 or not relevant_ids:
        return 0.0
    top_k = recommended_ids[:k]

    # DCG
    dcg = 0.0
    for i, rid in enumerate(top_k):
        rel = 1.0 if rid in relevant_ids else 0.0
        dcg += rel / math.log2(i + 2)  # i+2 because position is 1-indexed

    # Ideal DCG – place all relevant items at the top
    ideal_length = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_length))

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def rmse(predicted: List[float], actual: List[float]) -> float:
    """Root Mean Square Error between predicted and actual values."""
    if not predicted or not actual or len(predicted) != len(actual):
        return 0.0
    errors = [(p - a) ** 2 for p, a in zip(predicted, actual)]
    return math.sqrt(sum(errors) / len(errors))


def mae(predicted: List[float], actual: List[float]) -> float:
    """Mean Absolute Error between predicted and actual values."""
    if not predicted or not actual or len(predicted) != len(actual):
        return 0.0
    errors = [abs(p - a) for p, a in zip(predicted, actual)]
    return sum(errors) / len(errors)


# ═══════════════════════════════════════════════════════════════════════════
#  Train / test split
# ═══════════════════════════════════════════════════════════════════════════

def temporal_train_test_split(
    ratings: List[Dict[str, Any]], train_ratio: float = 0.80
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split ratings into train / test sets by timestamp (oldest → newest).

    If a rating has no ``timestamp`` field it is placed in the training set.
    """
    # Separate ratings with and without timestamps
    with_ts: List[Dict[str, Any]] = []
    without_ts: List[Dict[str, Any]] = []

    for r in ratings:
        ts = r.get("timestamp") or r.get("created_at") or r.get("date")
        if ts is not None:
            with_ts.append(r)
        else:
            without_ts.append(r)

    # Sort chronologically
    with_ts.sort(key=lambda r: r.get("timestamp") or r.get("created_at") or r.get("date"))

    split_idx = int(len(with_ts) * train_ratio)
    train = without_ts + with_ts[:split_idx]
    test = with_ts[split_idx:]

    return train, test


# ═══════════════════════════════════════════════════════════════════════════
#  Per-user recommendation generation
# ═══════════════════════════════════════════════════════════════════════════

def _generate_recommendations(
    user_id: str,
    alpha: float,
    train_ratings: List[Dict[str, Any]],
    feature_matrix: Any,
    rest_ids: List[str],
    rating_matrix: Any,
    k: int,
) -> List[Dict[str, Any]]:
    """Generate top-K recommendations for *user_id* using the given alpha."""

    # Content-based scores
    user_profile = build_user_profile(user_id, train_ratings, feature_matrix, rest_ids)
    content_scores = content_engine.compute_scores(user_profile, feature_matrix)

    # Collaborative scores
    collab_scores = collab_engine.compute_scores(user_id, rating_matrix)

    # Visited restaurants in the *training* set only
    visited_ids = {
        str(r.get("restaurant_id"))
        for r in train_ratings
        if str(r.get("user_id")) == user_id
    }

    scored_items = hybrid_engine.compute_hybrid_scores(
        content_scores=content_scores,
        collab_scores=collab_scores,
        alpha=alpha,
        visited_ids=visited_ids,
        all_restaurant_ids=rest_ids,
    )

    return hybrid_engine.get_top_n(scored_items, k)


# ═══════════════════════════════════════════════════════════════════════════
#  Main evaluation driver
# ═══════════════════════════════════════════════════════════════════════════

def run_evaluation(k: int = 10) -> Dict[str, Any]:
    """Execute the full offline evaluation pipeline.

    1. Load all ratings from MongoDB (pymongo sync).
    2. 80/20 temporal train/test split.
    3. For each user with test ratings, generate recommendations under each
       strategy (content-only, collaborative-only, hybrid).
    4. Compute Precision@K, Recall@K, NDCG@K, RMSE, MAE per strategy.
    5. Compute catalogue Coverage per strategy.

    Returns a JSON-serialisable dict.
    """
    db = get_sync_db()

    # ── Load data ──────────────────────────────────────────────────────────
    all_ratings_raw: List[Dict[str, Any]] = list(db.ratings.find({}))
    all_restaurants_raw: List[Dict[str, Any]] = list(db.restaurants.find({}))

    if not all_ratings_raw or not all_restaurants_raw:
        return {
            "k": k,
            "total_users_evaluated": 0,
            "strategies": {name: {} for name in STRATEGIES},
            "coverage": {name: 0.0 for name in STRATEGIES},
            "error": "Insufficient data – no ratings or no restaurants found.",
        }

    # Stringify ObjectIds for consistency with the engine code
    for r in all_ratings_raw:
        r["user_id"] = str(r.get("user_id", ""))
        r["restaurant_id"] = str(r.get("restaurant_id", ""))

    for rest in all_restaurants_raw:
        rest["_id"] = str(rest["_id"])

    total_restaurant_ids: Set[str] = {str(r["_id"]) for r in all_restaurants_raw}

    # ── Train / test split ─────────────────────────────────────────────────
    train_ratings, test_ratings = temporal_train_test_split(all_ratings_raw)

    if not test_ratings:
        return {
            "k": k,
            "total_users_evaluated": 0,
            "strategies": {name: {} for name in STRATEGIES},
            "coverage": {name: 0.0 for name in STRATEGIES},
            "error": "No test ratings after temporal split – add timestamps to ratings.",
        }

    # Build structures from *training* data only
    feature_matrix, rest_ids = build_restaurant_feature_matrix(all_restaurants_raw)
    rating_matrix = collab_engine.build_rating_matrix(train_ratings)

    # Group test ratings by user
    test_by_user: Dict[str, List[Dict[str, Any]]] = {}
    for r in test_ratings:
        uid = r["user_id"]
        test_by_user.setdefault(uid, []).append(r)

    # ── Accumulators ───────────────────────────────────────────────────────
    strategy_metrics: Dict[str, Dict[str, List[float]]] = {
        name: {
            "precision": [],
            "recall": [],
            "ndcg": [],
            "rmse_preds": [],
            "rmse_actuals": [],
            "mae_preds": [],
            "mae_actuals": [],
        }
        for name in STRATEGIES
    }
    recommended_catalogue: Dict[str, Set[str]] = {name: set() for name in STRATEGIES}

    users_evaluated = 0

    # ── Per-user evaluation ────────────────────────────────────────────────
    for user_id, user_test_ratings in test_by_user.items():
        # Relevant items in the test set (rated >= RELEVANCE_THRESHOLD)
        relevant_ids: Set[str] = {
            r["restaurant_id"]
            for r in user_test_ratings
            if float(r.get("score", 0)) >= RELEVANCE_THRESHOLD
        }

        # Actual ratings keyed by restaurant_id for error metrics
        actual_map: Dict[str, float] = {
            r["restaurant_id"]: float(r.get("score", 0))
            for r in user_test_ratings
        }

        if not relevant_ids:
            # If this user has no relevant items, skip to avoid inflating
            # precision/recall denominators.
            continue

        users_evaluated += 1

        for strategy_name, alpha in STRATEGIES.items():
            recs = _generate_recommendations(
                user_id=user_id,
                alpha=alpha,
                train_ratings=train_ratings,
                feature_matrix=feature_matrix,
                rest_ids=rest_ids,
                rating_matrix=rating_matrix,
                k=k,
            )

            rec_ids = [item["restaurant_id"] for item in recs]

            # Track catalogue coverage
            recommended_catalogue[strategy_name].update(rec_ids)

            # IR metrics
            strategy_metrics[strategy_name]["precision"].append(
                precision_at_k(rec_ids, relevant_ids, k)
            )
            strategy_metrics[strategy_name]["recall"].append(
                recall_at_k(rec_ids, relevant_ids, k)
            )
            strategy_metrics[strategy_name]["ndcg"].append(
                ndcg_at_k(rec_ids, relevant_ids, k)
            )

            # Rating-prediction error metrics
            # Map hybrid_score (0-1) → rating scale (1-5)
            for item in recs:
                rid = item["restaurant_id"]
                if rid in actual_map:
                    predicted_rating = 1.0 + item["hybrid_score"] * 4.0  # scale [0,1] → [1,5]
                    strategy_metrics[strategy_name]["rmse_preds"].append(predicted_rating)
                    strategy_metrics[strategy_name]["rmse_actuals"].append(actual_map[rid])
                    strategy_metrics[strategy_name]["mae_preds"].append(predicted_rating)
                    strategy_metrics[strategy_name]["mae_actuals"].append(actual_map[rid])

    # ── Aggregate results ──────────────────────────────────────────────────
    def _safe_mean(values: List[float]) -> float:
        return round(float(np.mean(values)), 4) if values else 0.0

    results: Dict[str, Any] = {
        "k": k,
        "total_users_evaluated": users_evaluated,
        "strategies": {},
        "coverage": {},
    }

    for name in STRATEGIES:
        m = strategy_metrics[name]
        results["strategies"][name] = {
            "precision_at_k": _safe_mean(m["precision"]),
            "recall_at_k": _safe_mean(m["recall"]),
            "ndcg_at_k": _safe_mean(m["ndcg"]),
            "rmse": round(rmse(m["rmse_preds"], m["rmse_actuals"]), 4),
            "mae": round(mae(m["mae_preds"], m["mae_actuals"]), 4),
        }

        # Coverage: fraction of total catalogue recommended across all users
        if total_restaurant_ids:
            results["coverage"][name] = round(
                len(recommended_catalogue[name]) / len(total_restaurant_ids), 4
            )
        else:
            results["coverage"][name] = 0.0

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  CLI entry-point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  Hybrid Restaurant Recommender – Offline Evaluation")
    print("=" * 70)
    print()

    results = run_evaluation(k=10)
    print(json.dumps(results, indent=2))
