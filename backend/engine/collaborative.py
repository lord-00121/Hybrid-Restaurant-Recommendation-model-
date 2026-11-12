from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD

from engine.preprocess import normalize_scores


class CollaborativeEngine:
    """User-based Collaborative Filtering engine with Pearson correlation

    and TruncatedSVD fallback for sparse data.
    """

    def __init__(self) -> None:
        pass

    def build_rating_matrix(self, ratings: List[Dict[str, Any]]) -> pd.DataFrame:
        """Pivots list of rating dicts into a user_id x restaurant_id matrix.

        Returns:
            pd.DataFrame where rows are user_ids, columns are restaurant_ids,
            and values are numerical ratings (with NaN for unrated pairs).
        """
        if not ratings:
            return pd.DataFrame()

        clean_ratings = []
        for r in ratings:
            uid = str(r.get("user_id", ""))
            rid = str(r.get("restaurant_id", ""))
            score = r.get("score")
            if uid and rid and score is not None:
                clean_ratings.append({
                    "user_id": uid,
                    "restaurant_id": rid,
                    "score": float(score),
                })

        if not clean_ratings:
            return pd.DataFrame()

        df = pd.DataFrame(clean_ratings)
        rating_matrix = df.pivot_table(
            index="user_id",
            columns="restaurant_id",
            values="score",
            aggfunc="mean",
        )
        return rating_matrix

    def _svd_fallback(
        self, target_user_id: str, rating_matrix: pd.DataFrame
    ) -> Dict[str, float]:
        """Matrix factorization fallback using TruncatedSVD for sparse datasets."""
        n_users = len(rating_matrix)
        if n_users <= 1:
            return {}

        n_components = max(1, min(10, n_users - 1))
        # Fill missing values with user mean or 0
        matrix_filled = rating_matrix.apply(lambda row: row.fillna(row.mean() if not np.isnan(row.mean()) else 3.0), axis=1)
        matrix_filled = matrix_filled.fillna(3.0)

        svd = TruncatedSVD(n_components=n_components, random_state=42)
        reduced = svd.fit_transform(matrix_filled.values)
        reconstructed = svd.inverse_transform(reduced)

        pred_df = pd.DataFrame(
            reconstructed,
            index=rating_matrix.index,
            columns=rating_matrix.columns,
        )

        user_preds = pred_df.loc[target_user_id].values
        norm_preds = normalize_scores(user_preds)

        return {
            str(col): float(val)
            for col, val in zip(rating_matrix.columns, norm_preds)
        }

    def compute_scores(
        self, target_user_id: str, rating_matrix: pd.DataFrame
    ) -> Dict[str, float]:
        """Computes collaborative filtering prediction scores for the target user.

        - If target user has < 3 ratings, returns empty dict.
        - If matrix has < 10 users, uses TruncatedSVD fallback.
        - Otherwise, computes Pearson correlation with all users, selects top 20,
          and predicts restaurant scores as weighted average of ratings.
        - Normalizes all scores to [0, 1].
        """
        target_uid = str(target_user_id)

        if rating_matrix.empty or target_uid not in rating_matrix.index:
            return {}

        target_row = rating_matrix.loc[target_uid].dropna()
        if len(target_row) < 3:
            return {}

        n_users = len(rating_matrix)

        # Fallback to TruncatedSVD if matrix is very sparse (< 10 rated users total)
        if n_users < 10:
            return self._svd_fallback(target_uid, rating_matrix)

        # User-based Collaborative Filtering with Pearson Correlation
        target_ratings = rating_matrix.loc[target_uid]
        target_mean = float(target_ratings.mean())

        similarities: List[Tuple[str, float]] = []

        for other_uid in rating_matrix.index:
            if other_uid == target_uid:
                continue

            other_ratings = rating_matrix.loc[other_uid]
            # Co-rated items
            common = target_ratings.notna() & other_ratings.notna()
            if common.sum() < 2:
                continue

            u_common = target_ratings[common]
            v_common = other_ratings[common]

            # Standard deviation check to prevent division by zero in correlation
            if float(u_common.std(ddof=0)) == 0.0 or float(v_common.std(ddof=0)) == 0.0:
                continue

            corr = u_common.corr(v_common)
            if pd.notna(corr) and corr > 0:
                similarities.append((str(other_uid), float(corr)))

        # If Pearson correlation found no similar users due to sparsity, fallback to SVD
        if not similarities:
            return self._svd_fallback(target_uid, rating_matrix)

        # Sort and take top 20 similar users
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similar = similarities[:20]

        all_restaurant_ids = rating_matrix.columns
        predicted_scores = []

        for rest_id in all_restaurant_ids:
            weighted_sum = 0.0
            weights_sum = 0.0

            for sim_uid, sim_score in top_similar:
                sim_rating = rating_matrix.loc[sim_uid, rest_id]
                if pd.notna(sim_rating):
                    weighted_sum += sim_score * float(sim_rating)
                    weights_sum += sim_score

            if weights_sum > 0.0:
                pred_rating = weighted_sum / weights_sum
            else:
                # Fallback to column mean or user baseline
                col_mean = rating_matrix[rest_id].mean()
                pred_rating = float(col_mean) if pd.notna(col_mean) else target_mean

            predicted_scores.append(pred_rating)

        norm_scores = normalize_scores(np.array(predicted_scores))

        return {
            str(rest_id): float(score)
            for rest_id, score in zip(all_restaurant_ids, norm_scores)
        }
