import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
INPUT_FILE = DATA_DIR / "tufs-vocab.tsv"

OUTPUT_FILE = DATA_DIR / "multilingual_vocabulary.csv"

LANGUAGES = ["en", "ar", "fr", "es", "de", "zh", "ja"]

print("Loading TUFS dataset...")

df = pd.read_csv(
    INPUT_FILE,
    sep="\t",
    dtype={"cid": "string"}
)

# Keep our seven target languages
df = df[df["lang"].isin(LANGUAGES)].copy()

# Remove entries without a concept ID or vocabulary word
df = df.dropna(subset=["cid", "lemma"])

# Remove empty words
df["lemma"] = df["lemma"].astype(str).str.strip()
df = df[df["lemma"] != ""]

print("\nEntries per language with concept IDs:")
print(df["lang"].value_counts())

# Group words belonging to the same concept and language
grouped = (
    df.groupby(["cid", "lang"])["lemma"]
    .agg(lambda words: " / ".join(dict.fromkeys(words)))
    .unstack("lang")
)

# Ensure all seven language columns exist
grouped = grouped.reindex(columns=LANGUAGES)

# Count how many languages represent each concept
grouped["languages_present"] = grouped[LANGUAGES].notna().sum(axis=1)

# Keep concepts represented in at least two languages
shared = grouped[grouped["languages_present"] >= 2].copy()

shared.reset_index(inplace=True)

shared.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("\nExtraction completed!")
print("Total shared concepts:", len(shared))

print("\nConcept coverage:")
for count in [2, 3, 4, 5, 6, 7]:
    total = (grouped["languages_present"] == count).sum()
    print(f"Concepts available in {count} languages: {total}")

print("\nSample extracted concepts:")
print(shared.head(10).to_string(index=False))

print(f"\nSaved to: {OUTPUT_FILE}")