
import re
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
DATA_DIR = Path(__file__).resolve().parent
DATASET_PATH = DATA_DIR / "topic_vocabulary.csv"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

LANGUAGES = ["en", "ar", "fr", "es", "de", "zh", "ja"]

print("Loading vocabulary dataset...")
df = pd.read_csv(DATASET_PATH)

def clean_word(word):
    """Remove additional linguistic metadata from vocabulary entries."""

    word = str(word).strip()

    # Remove metadata inside parentheses.
    word = re.sub(r"\s*\([^)]*\)", "", word)

    return word.strip()

df["lemma"] = df["lemma"].apply(clean_word)

df = df[
    df["lemma"].notna()
    & (df["lemma"].str.len() > 0)
]

# --------------------------------------------------
# 3. Load multilingual embedding model
# --------------------------------------------------

print("Loading multilingual embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("Model loaded successfully!")


# --------------------------------------------------
# 4. Vocabulary prediction function
# --------------------------------------------------

def recommend_words(sentence, topic, target_lang, top_k=10):

    if target_lang not in LANGUAGES:
        raise ValueError(f"Unsupported language: {target_lang}")

    # Retrieve vocabulary belonging to the requested topic/language.
    candidates = df[
        (df["topic"] == topic)
        & (df["lang"] == target_lang)
    ].copy()

    candidates = candidates.drop_duplicates(subset=["lemma"])

    if candidates.empty:
        print(f"No vocabulary found for {topic} in {target_lang}.")
        return []

    words = candidates["lemma"].tolist()

    # Convert the sentence and vocabulary words into embeddings.
    sentence_embedding = model.encode(
        sentence,
        convert_to_tensor=True
    )

    word_embeddings = model.encode(
        words,
        convert_to_tensor=True
    )

    # Calculate semantic similarity.
    similarities = util.cos_sim(
        sentence_embedding,
        word_embeddings
    )[0]

    # Rank words from highest to lowest similarity.
    ranked_indices = similarities.argsort(
        descending=True
    )[:top_k]

    results = []

    for index in ranked_indices:
        results.append({
            "word": words[int(index)],
            "score": round(float(similarities[int(index)]), 4)
        })

    return results


# --------------------------------------------------
# 5. Test the prediction function
# --------------------------------------------------

if __name__ == "__main__":

    sentence = "أخطط لرحلة إلى باريس في الصيف القادم."

    topic = "Travel"
    target_lang = "ar"

    print("\nPREDICTION TEST")
    print("Sentence:", sentence)
    print("Topic:", topic)
    print("Target language:", target_lang)

    predictions = recommend_words(
    sentence=sentence,
    topic=topic,
    target_lang=target_lang,
    top_k=30)


    print("\nRecommended vocabulary:")

    for item in predictions:
        print(f"{item['word']}  |  Score: {item['score']}")

    # Export predictions for human evaluation
    evaluation_data = pd.DataFrame(predictions)

    evaluation_data["sentence"] = sentence
    evaluation_data["topic"] = topic
    evaluation_data["target_lang"] = target_lang

    # Leave labels empty for manual annotation
    evaluation_data["relevance"] = ""

    output_file = DATA_DIR / "prediction_evaluation.csv"

    evaluation_data.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nEvaluation file saved to: {output_file}")