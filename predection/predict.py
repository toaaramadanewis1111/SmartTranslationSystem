
import re
import joblib
import pandas as pd

from pathlib import Path
from sentence_transformers import SentenceTransformer


# =========================================================
# 1. PROJECT PATHS AND CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "vocabulary_ranker.pkl"
VOCAB_PATH = BASE_DIR / "topic_vocabulary.csv"

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

DEFAULT_TOP_K = 5


# =========================================================
# 2. TEXT PROCESSING
# =========================================================

def tokenize(text):
    """
    Extract words from text.

    Used for lexical overlap and candidate length.
    """

    if pd.isna(text):
        return []

    return re.findall(r"\b\w+\b", str(text).lower())


def calculate_lexical_overlap(sentence, candidate):
    """
    Calculate the overlap between sentence words
    and candidate words.

    Returns a value between 0 and 1.
    """

    sentence_words = set(tokenize(sentence))
    candidate_words = set(tokenize(candidate))

    if not candidate_words:
        return 0.0

    overlap = sentence_words.intersection(candidate_words)

    return len(overlap) / len(candidate_words)


# =========================================================
# 3. VOCABULARY PREDICTOR
# =========================================================

class VocabularyPredictor:

    def __init__(self):

        print("Loading vocabulary prediction model...")

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}"
            )

        if not VOCAB_PATH.exists():
            raise FileNotFoundError(
                f"Vocabulary dataset not found: {VOCAB_PATH}"
            )

        # Load trained LightGBM model and configuration
        self.bundle = joblib.load(MODEL_PATH)

        self.model = self.bundle["model"]

        self.feature_names = self.bundle["features"]

        embedding_model_name = self.bundle.get(
            "embedding_model",
            EMBEDDING_MODEL_NAME
        )

        # Load multilingual embedding model
        print("Loading multilingual embedding model...")

        self.embedding_model = SentenceTransformer(
            embedding_model_name,
            device="cpu"
        )

        # Load vocabulary dataset
        self.vocabulary = pd.read_csv(VOCAB_PATH)

        # Required dataset columns
        required_columns = {
            "lemma",
            "lang",
            "topic"
        }

        missing_columns = required_columns - set(
            self.vocabulary.columns
        )

        if missing_columns:
            raise ValueError(
                f"Missing vocabulary columns: {missing_columns}"
            )

        # Validate feature names
        expected_features = [
            "sentence_similarity",
            "topic_similarity",
            "lexical_overlap",
            "candidate_length"
        ]

        if set(self.feature_names) != set(expected_features):
            raise ValueError(
                "Feature mismatch!\n"
                f"Model features: {self.feature_names}\n"
                f"Expected features: {expected_features}"
            )

        print("Vocabulary predictor ready!")
        print(
            f"Vocabulary entries: {len(self.vocabulary)}"
        )

    # =====================================================
    # 4. FILTER CANDIDATES
    # =====================================================

    def get_candidates(self, target_lang, topic):

        candidates = self.vocabulary[
            (self.vocabulary["lang"] == target_lang) &
            (self.vocabulary["topic"] == topic)
        ].copy()

        if candidates.empty:
            candidates = self.vocabulary[
                self.vocabulary["lang"] == target_lang
            ].copy()

        candidates = candidates.dropna(
            subset=["lemma"]
        )

        candidates = candidates.drop_duplicates(
            subset=["lemma"]
        )

        candidates = candidates.reset_index(drop=True)

        return candidates

    # =====================================================
    # 5. GENERATE FEATURES
    # =====================================================

    def generate_features(
        self,
        sentence,
        topic,
        candidates,
        context=None
    ):

        candidate_words = candidates["lemma"].astype(str).tolist()
        contextual_sentence = " ".join(
            value.strip()
            for value in (sentence, context)
            if value and value.strip()
        )

        # Generate normalized sentence embedding
        sentence_embedding = self.embedding_model.encode(
            [contextual_sentence],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        # Generate normalized topic embedding
        topic_embedding = self.embedding_model.encode(
            [topic],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        # Generate normalized candidate embeddings
        candidate_embeddings = self.embedding_model.encode(
            candidate_words,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False
        )

        # Cosine similarities using normalized embeddings
        sentence_similarities = (
            candidate_embeddings @ sentence_embedding
        )

        topic_similarities = (
            candidate_embeddings @ topic_embedding
        )

        # Calculate remaining features
        lexical_overlaps = [
            calculate_lexical_overlap(contextual_sentence, word)
            for word in candidate_words
        ]

        candidate_lengths = [
            len(tokenize(word))
            for word in candidate_words
        ]

        # Build feature dataframe
        features_df = pd.DataFrame({

            "sentence_similarity": sentence_similarities,

            "topic_similarity": topic_similarities,

            "lexical_overlap": lexical_overlaps,

            "candidate_length": candidate_lengths

        })

        # Preserve the exact feature order used during training
        features_df = features_df[self.feature_names]

        return features_df

    # =====================================================
    # 6. DIAGNOSTIC REPORT
    # =====================================================

    def print_diagnostic_report(
        self,
        candidates,
        features_df,
        scores
    ):

        results = candidates.copy()

        results["score"] = scores

        # Attach calculated features
        for column in self.feature_names:

            results[column] = features_df[
                column
            ].values

        # Sort all candidates by score
        results = results.sort_values(
            by="score",
            ascending=False
        ).reset_index(drop=True)

        print("\n")
        print("=" * 70)
        print("ALL CANDIDATES — DIAGNOSTIC REPORT")
        print("=" * 70)

        for index, row in results.iterrows():

            print("\n" + "-" * 70)

            print(f"Rank: {index + 1}")

            print(f"Word: {row['lemma']}")

            print(f"Score: {row['score']:.4f}")

            print(
                "Sentence similarity:",
                f"{row['sentence_similarity']:.4f}"
            )

            print(
                "Topic similarity:",
                f"{row['topic_similarity']:.4f}"
            )

            print(
                "Lexical overlap:",
                f"{row['lexical_overlap']:.4f}"
            )

            print(
                "Candidate length:",
                row["candidate_length"]
            )

            # Dataset metadata
            if "is_basic" in results.columns:
                print("Basic:", row["is_basic"])

            if "scenes" in results.columns:
                print("Scenes:", row["scenes"])

            if "examples" in results.columns:

                example = row["examples"]

                if pd.isna(example):
                    example = "No examples available"

                print("Examples:", str(example)[:500])

        print("\n" + "=" * 70)
        print("END OF DIAGNOSTIC REPORT")
        print("=" * 70)

        return results

    # =====================================================
    # 7. PREDICTION
    # =====================================================

    def predict(
        self,
        sentence,
        topic,
        target_lang,
        top_k=DEFAULT_TOP_K,
        context=None
    ):

        # Get vocabulary candidates
        candidates = self.get_candidates(
            target_lang,
            topic
        )

        if candidates.empty:
            return []

        # Generate prediction features
        features_df = self.generate_features(
            sentence,
            topic,
            candidates,
            context=context
        )

        # Predict relevance scores
        scores = self.model.predict_proba(
            features_df
        )[:, 1]

        candidates["score"] = scores
        top_results = candidates.sort_values(
            by="score",
            ascending=False
        ).head(top_k)

        recommendations = [
            {
                "word": row["lemma"],
                "score": float(row["score"])
            }
            for _, row in top_results.iterrows()
        ]

        return recommendations


# =========================================================
# 8. RUN TEST
# =========================================================

if __name__ == "__main__":

    predictor = VocabularyPredictor()

    test_sentence = (
        "أخطط لرحلة إلى باريس في الصيف القادم."
    )

    test_topic = "Travel"

    test_language = "ar"

    predictions = predictor.predict(
        sentence=test_sentence,
        topic=test_topic,
        target_lang=test_language,
        top_k=5
    )
