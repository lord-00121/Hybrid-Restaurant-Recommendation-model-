from typing import Any, Dict, List, Set


class HybridEngine:
    """Hybrid recommendation engine combining Content-Based and Collaborative Filtering."""

    def __init__(self) -> None:
        pass

    def get_alpha(self, user_rating_count: int) -> float:
        """Determines the weighting factor alpha based on user rating history count.

        Rules:
            0 ratings  -> alpha = 1.0 (pure content-based / cold start)
            1-4 ratings -> alpha = 0.75 (strong content preference)
            5-9 ratings -> alpha = 0.60 (balanced with emerging CF)
            >=10 ratings -> alpha = 0.50 (full hybrid blend)
        """
        if user_rating_count <= 0:
            return 1.0
        elif 1 <= user_rating_count <= 4:
            return 0.75
        elif 5 <= user_rating_count <= 9:
            return 0.60
        else:
            return 0.50

    def compute_hybrid_scores(
        self,
        content_scores: Dict[str, float],
        collab_scores: Dict[str, float],
        alpha: float,
        visited_ids: Set[str],
        all_restaurant_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """Calculates hybrid scores for candidate restaurants.

        Formula:
            Hybrid Score = alpha * Content Score + (1 - alpha) * Collaborative Score
            (Uses 0.5 as default score if a model has no prediction for an item)

        Excludes visited restaurants unless all candidate restaurants have been visited.

        Returns:
            Sorted list of dicts with restaurant_id, hybrid_score, content_score,
            collab_score, and reason.
        """
        visited_set = {str(vid) for vid in visited_ids}

        # Determine explanation reason based on alpha weight
        if alpha > 0.7:
            reason = "Based on your preferences"
        elif alpha < 0.4:
            reason = "Liked by people like you"
        else:
            reason = "Personalized for you"

        # Exclude visited restaurants unless all would be filtered out
        candidate_ids = [rid for rid in all_restaurant_ids if str(rid) not in visited_set]
        if not candidate_ids:
            candidate_ids = list(all_restaurant_ids)

        scored_list: List[Dict[str, Any]] = []

        for rid in candidate_ids:
            str_rid = str(rid)
            c_score = float(content_scores.get(str_rid, 0.5))
            col_score = float(collab_scores.get(str_rid, 0.5))

            h_score = (alpha * c_score) + ((1.0 - alpha) * col_score)

            scored_list.append({
                "restaurant_id": str_rid,
                "hybrid_score": round(float(h_score), 4),
                "content_score": round(float(c_score), 4),
                "collab_score": round(float(col_score), 4),
                "reason": reason,
            })

        # Sort descending by hybrid_score
        scored_list.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return scored_list

    def get_top_n(self, scored_list: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
        """Returns the top N scored items from the candidate list."""
        if n <= 0:
            return []
        return scored_list[:n]
