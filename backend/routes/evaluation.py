"""
Evaluation API Route
====================
Exposes the offline benchmarking pipeline as a REST endpoint so metrics can be
retrieved from the frontend admin dashboard or CI scripts.
"""

from fastapi import APIRouter, Query

from evaluation import run_evaluation

router = APIRouter()


@router.get("")
async def evaluate(
    k: int = Query(10, ge=1, le=100, description="Number of recommendations (K) to evaluate"),
):
    """Run the offline evaluation and return JSON metrics.

    Returns precision@K, recall@K, NDCG@K, RMSE, MAE, and catalogue coverage
    for three strategies: content-only, collaborative-only, and hybrid.
    """
    # run_evaluation is CPU-bound / synchronous – acceptable for an admin
    # endpoint that is called infrequently.
    results = run_evaluation(k=k)
    return results
