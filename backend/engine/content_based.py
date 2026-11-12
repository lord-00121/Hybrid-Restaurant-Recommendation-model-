from typing import Dict
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from engine.preprocess import normalize_scores


class ContentBasedEngine:
    """Content-based recommendation engine based on cosine similarity."""

    def __init__(self) -> None:
        pass

    def compute_scores(
        self, user_profile: np.ndarray, feature_matrix: pd.DataFrame
    ) -> Dict[str, float]:
        """Computes content-based similarity scores between user profile and restaurants.

        Args:
            user_profile: 1D numpy array representing user preference vector.
            feature_matrix: DataFrame of restaurant feature vectors indexed by restaurant_id.

        Returns:
            Dict mapping restaurant_id to normalized score in [0, 1].
        """
        if feature_matrix.empty:
            return {}

        # Handle cold-start or empty user profile: return equal scores (0.5)
        profile_norm = np.linalg.norm(user_profile)
        if profile_norm == 0 or np.all(user_profile == 0):
            return {str(rest_id): 0.5 for rest_id in feature_matrix.index}

        user_vec = user_profile.reshape(1, -1)
        sims = cosine_similarity(user_vec, feature_matrix.values).flatten()

        # Min-max normalize scores to [0, 1]
        normalized_sims = normalize_scores(sims)

        return {
            str(rest_id): float(score)
            for rest_id, score in zip(feature_matrix.index, normalized_sims)
        }
