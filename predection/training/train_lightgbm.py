
import re
import gc
import random
import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb

from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    roc_auc_score
)


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_PATH = BASE_DIR / "topic_vocabulary.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "vocabulary_ranker.pkl"

EMBEDDING_MODEL_NAME = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

BATCH_SIZE = 16
NEGATIVES_PER_POSITIVE = 5
RANDOM_STATE = 42

FEATURES = [
    "sentence_similarity",
    "topic_similarity",
    "lexical_overlap",
    "candidate_length"
]

random.seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. TEXT CLEANING
# ============================================================

def clean_word(word):
    """Remove extra whitespace and parenthetical metadata."""

    if pd.isna(word):
        return ""

    word = str(word).strip()

    # Remove metadata such as (morph:...)
    word = re.sub(r"\s*\([^)]*\)", "", word)

    return word.strip()


def parse_examples(value):
    """Extract individual example sentences from a TUFS cell."""

    if pd.isna(value):
        return []

    examples = str(value).split(";;;")

    cleaned = []

    for example in examples:
        example = example.strip()

        if len(example) >= 3:
            cleaned.append(example)

    return cleaned


def tokenize(text):
    """Extract Unicode word tokens."""

    return set(re.findall(r"[^\W_]+", str(text).lower()))


# ============================================================
# 3. LOAD VOCABULARY DATASET
# ============================================================

def load_vocabulary():

    print("\nLoading TUFS vocabulary...")

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    required_columns = [
        "lemma",
        "lang",
        "topic",
        "examples"
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing dataset columns: {missing}"
        )

    df["lemma"] = df["lemma"].apply(clean_word)
    df["lang"] = df["lang"].astype(str).str.strip()
    df["topic"] = df["topic"].astype(str).str.strip()

    df = df[
        (df["lemma"] != "") &
        (df["lang"] != "") &
        (df["topic"] != "") &
        (df["topic"] != "nan")
    ].reset_index(drop=True)

    print(f"Vocabulary entries: {len(df)}")

    return df


# ============================================================
# 4. GENERATE TRAINING PAIRS
# ============================================================

def generate_training_pairs(vocabulary):

    print("\nGenerating training examples...")

    # Group vocabulary by topic and language.
    grouped_candidates = {}

    for (topic, lang), group in vocabulary.groupby(
        ["topic", "lang"]
    ):

        grouped_candidates[(topic, lang)] = (
            group.index.tolist()
        )

    training_rows = []

    for idx, row in vocabulary.iterrows():

        sentence_examples = parse_examples(
            row["examples"]
        )

        if not sentence_examples:
            continue

        positive_candidate = row["lemma"]
        topic = row["topic"]
        lang = row["lang"]

        candidate_indices = grouped_candidates.get(
            (topic, lang), []
        )

        # Avoid using the positive vocabulary word as a negative.
        negative_pool = [
            candidate_idx
            for candidate_idx in candidate_indices
            if candidate_idx != idx
            and vocabulary.iloc[candidate_idx]["lemma"]
            != positive_candidate
        ]

        if not negative_pool:
            continue

        for sentence in sentence_examples:

            # Positive pair:
            # The vocabulary word is associated with its example.
            training_rows.append({
                "sentence": sentence,
                "candidate": positive_candidate,
                "topic": topic,
                "lang": lang,
                "label": 1
            })

            # Negative pairs:
            # Random vocabulary candidates from the same topic
            # and language.
            number_of_negatives = min(
                NEGATIVES_PER_POSITIVE,
                len(negative_pool)
            )

            sampled_negatives = random.sample(
                negative_pool,
                number_of_negatives
            )

            for negative_idx in sampled_negatives:

                negative_candidate = vocabulary.iloc[
                    negative_idx
                ]["lemma"]

                training_rows.append({
                    "sentence": sentence,
                    "candidate": negative_candidate,
                    "topic": topic,
                    "lang": lang,
                    "label": 0
                })

    training_df = pd.DataFrame(training_rows)

    if training_df.empty:
        raise ValueError(
            "No training pairs generated. "
            "Check the examples column in your dataset."
        )

    print(
        f"Generated training pairs: {len(training_df)}"
    )

    print("\nLabel distribution:")
    print(training_df["label"].value_counts())

    return training_df


# ============================================================
# 5. LOAD MULTILINGUAL EMBEDDING MODEL
# ============================================================

def load_embedding_model():

    print("\nLoading multilingual embedding model...")

    model = SentenceTransformer(
        EMBEDDING_MODEL_NAME,
        device="cpu"
    )

    print("Embedding model loaded!")

    return model


# ============================================================
# 6. ENCODE UNIQUE TEXTS ONLY
# ============================================================

def encode_unique_texts(model, texts, description):

    unique_texts = list(dict.fromkeys(texts))

    print(
        f"\nEncoding {description}: "
        f"{len(unique_texts)} unique texts"
    )

    embeddings = model.encode(
        unique_texts,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return unique_texts, embeddings


# ============================================================
# 7. FEATURE EXTRACTION
# ============================================================

def extract_features(training_df, embedding_model):

    print("\nGenerating semantic features...")

    # Encode each unique sentence only once.
    unique_sentences, sentence_embeddings = (
        encode_unique_texts(
            embedding_model,
            training_df["sentence"].tolist(),
            "sentences"
        )
    )

    # Encode each unique vocabulary candidate only once.
    unique_candidates, candidate_embeddings = (
        encode_unique_texts(
            embedding_model,
            training_df["candidate"].tolist(),
            "candidates"
        )
    )

    # Encode each unique topic only once.
    unique_topics, topic_embeddings = (
        encode_unique_texts(
            embedding_model,
            training_df["topic"].tolist(),
            "topics"
        )
    )

    # Map every training row to its corresponding embedding.
    sentence_to_idx = {
        text: idx
        for idx, text in enumerate(unique_sentences)
    }

    candidate_to_idx = {
        text: idx
        for idx, text in enumerate(unique_candidates)
    }

    topic_to_idx = {
        text: idx
        for idx, text in enumerate(unique_topics)
    }

    sentence_indices = np.array([
        sentence_to_idx[text]
        for text in training_df["sentence"]
    ], dtype=np.int32)

    candidate_indices = np.array([
        candidate_to_idx[text]
        for text in training_df["candidate"]
    ], dtype=np.int32)

    topic_indices = np.array([
        topic_to_idx[text]
        for text in training_df["topic"]
    ], dtype=np.int32)

    number_of_rows = len(training_df)

    sentence_similarity = np.zeros(
        number_of_rows,
        dtype=np.float32
    )

    topic_similarity = np.zeros(
        number_of_rows,
        dtype=np.float32
    )

    # --------------------------------------------------------
    # Calculate PAIRED cosine similarities in small batches.
    # No all-against-all similarity matrix is created.
    # --------------------------------------------------------

    print("\nCalculating paired cosine similarities...")

    FEATURE_BATCH_SIZE = 4096

    for start in range(
        0,
        number_of_rows,
        FEATURE_BATCH_SIZE
    ):

        end = min(
            start + FEATURE_BATCH_SIZE,
            number_of_rows
        )

        s_idx = sentence_indices[start:end]
        c_idx = candidate_indices[start:end]
        t_idx = topic_indices[start:end]

        # Sentence-to-candidate similarity.
        sentence_similarity[start:end] = np.sum(
            sentence_embeddings[s_idx] *
            candidate_embeddings[c_idx],
            axis=1
        )

        # Topic-to-candidate similarity.
        topic_similarity[start:end] = np.sum(
            topic_embeddings[t_idx] *
            candidate_embeddings[c_idx],
            axis=1
        )

    print("Semantic similarities calculated!")

    # --------------------------------------------------------
    # Lexical overlap and candidate length.
    # --------------------------------------------------------

    print("\nCalculating lexical features...")

    lexical_overlap = np.zeros(
        number_of_rows,
        dtype=np.float32
    )

    candidate_length = np.zeros(
        number_of_rows,
        dtype=np.float32
    )

    for i, (sentence, candidate) in enumerate(
        zip(
            training_df["sentence"],
            training_df["candidate"]
        )
    ):

        sentence_tokens = tokenize(sentence)
        candidate_tokens = tokenize(candidate)

        if candidate_tokens:
            overlap = (
                len(sentence_tokens & candidate_tokens)
                / len(candidate_tokens)
            )
        else:
            overlap = 0.0

        lexical_overlap[i] = overlap

        candidate_length[i] = len(candidate_tokens)

    # --------------------------------------------------------
    # Build final feature table.
    # --------------------------------------------------------

    features_df = pd.DataFrame({

        "sentence_similarity": sentence_similarity,

        "topic_similarity": topic_similarity,

        "lexical_overlap": lexical_overlap,

        "candidate_length": candidate_length

    })

    print("\nFeature extraction completed!")

    print("\nFeature preview:")
    print(features_df.head())

    print("\nFeature shape:", features_df.shape)

    # Release embedding memory before LightGBM training.
    del sentence_embeddings
    del candidate_embeddings
    del topic_embeddings

    gc.collect()

    return features_df


# ============================================================
# 8. TRAIN LIGHTGBM
# ============================================================

def train_model(training_df, features_df):

    print("\nPreparing LightGBM training data...")

    X = features_df[FEATURES]
    y = training_df["label"]

    # Keep examples from the same sentence together
    # to reduce train/test leakage.
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.2,
        random_state=RANDOM_STATE
    )

    train_indices, test_indices = next(
        splitter.split(
            X,
            y,
            groups=training_df["sentence"]
        )
    )

    X_train = X.iloc[train_indices]
    X_test = X.iloc[test_indices]

    y_train = y.iloc[train_indices]
    y_test = y.iloc[test_indices]

    print("\nTraining samples:", len(X_train))
    print("Testing samples:", len(X_test))

    print("\nTraining LightGBM classifier...")

    model = lgb.LGBMClassifier(

        objective="binary",

        n_estimators=300,

        learning_rate=0.05,

        num_leaves=15,

        max_depth=-1,

        class_weight="balanced",

        random_state=RANDOM_STATE,

        n_jobs=-1,

        verbosity=-1

    )

    model.fit(
        X_train,
        y_train
    )

    print("\nTraining completed!")

    return model, X_test, y_test


# ============================================================
# 9. EVALUATION
# ============================================================

def evaluate_model(model, X_test, y_test):

    print("\n" + "=" * 55)
    print("MODEL EVALUATION")
    print("=" * 55)

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print(f"\nAccuracy: {accuracy:.4f}")

    if y_test.nunique() == 2:

        auc = roc_auc_score(
            y_test,
            probabilities
        )

        print(f"ROC-AUC: {auc:.4f}")

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print("\nFeature Importances:")

    importance_df = pd.DataFrame({

        "Feature": FEATURES,

        "Importance": model.feature_importances_

    }).sort_values(
        by="Importance",
        ascending=False
    )

    print(importance_df.to_string(index=False))

    return accuracy


# ============================================================
# 10. SAVE TRAINED MODEL
# ============================================================

def save_model(model):

    print("\nSaving trained model...")

    model_bundle = {

        "model": model,

        "features": FEATURES,

        "embedding_model": EMBEDDING_MODEL_NAME,

        "model_type": "LightGBM vocabulary relevance classifier",

        "version": 1

    }

    joblib.dump(
        model_bundle,
        MODEL_PATH,
        compress=3
    )

    print("\nModel saved successfully!")

    print(f"Model path: {MODEL_PATH}")


# ============================================================
# 11. MAIN PIPELINE
# ============================================================

def main():

    print("\n" + "=" * 55)
    print("MyBTranslation - Vocabulary Prediction Training")
    print("=" * 55)

    # Step 1: Load dataset.
    vocabulary = load_vocabulary()

    # Step 2: Generate positive and negative pairs.
    training_df = generate_training_pairs(
        vocabulary
    )

    # Step 3: Load multilingual embedding model.
    embedding_model = load_embedding_model()

    # Step 4: Extract features.
    features_df = extract_features(
        training_df,
        embedding_model
    )

    # Release embedding model before training.
    del embedding_model
    gc.collect()

    # Step 5: Train LightGBM.
    model, X_test, y_test = train_model(
        training_df,
        features_df
    )

    # Step 6: Evaluate.
    evaluate_model(
        model,
        X_test,
        y_test
    )

    # Step 7: Save.
    save_model(model)

    print("\n" + "=" * 55)
    print("PIPELINE FINISHED SUCCESSFULLY!")
    print("=" * 55)


if __name__ == "__main__":

    main()
