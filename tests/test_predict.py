import unittest
from unittest.mock import Mock

import numpy as np
import pandas as pd

from predection.predict import VocabularyPredictor


class VocabularyPredictorTests(unittest.TestCase):
    def test_generate_features_includes_context_in_sentence_features(self):
        predictor = VocabularyPredictor.__new__(VocabularyPredictor)
        predictor.feature_names = [
            "sentence_similarity",
            "topic_similarity",
            "lexical_overlap",
            "candidate_length"
        ]
        predictor.embedding_model = Mock()
        predictor.embedding_model.encode.side_effect = [
            np.array([[1.0, 0.0]]),
            np.array([[0.0, 1.0]]),
            np.array([[1.0, 0.0]])
        ]
        candidates = pd.DataFrame({"lemma": ["station"]})

        features = predictor.generate_features(
            sentence="Bonjour",
            topic="Travel",
            candidates=candidates,
            context="We are looking for the train station."
        )

        self.assertEqual(
            predictor.embedding_model.encode.call_args_list[0].args[0],
            ["Bonjour We are looking for the train station."]
        )
        self.assertEqual(features.loc[0, "lexical_overlap"], 1.0)

    def test_predict_returns_ranked_recommendations(self):
        predictor = VocabularyPredictor.__new__(VocabularyPredictor)
        predictor.get_candidates = Mock(return_value=pd.DataFrame({
            "lemma": ["train", "gare", "ticket"]
        }))
        predictor.generate_features = Mock(return_value=pd.DataFrame())
        predictor.model = Mock()
        predictor.model.predict_proba.return_value = np.array([
            [0.8, 0.2],
            [0.1, 0.9],
            [0.5, 0.5]
        ])

        recommendations = predictor.predict(
            sentence="Où se trouve la gare ?",
            topic="Travel",
            target_lang="fr",
            top_k=2,
            context="The user is asking for directions at a railway station."
        )

        predictor.generate_features.assert_called_once_with(
            "Où se trouve la gare ?",
            "Travel",
            predictor.get_candidates.return_value,
            context="The user is asking for directions at a railway station."
        )
        self.assertEqual(
            recommendations,
            [
                {"word": "gare", "score": 0.9},
                {"word": "ticket", "score": 0.5}
            ]
        )


if __name__ == "__main__":
    unittest.main()
